"""
NEXUS GROUP - Rapports PDF Endpoints
=====================================
Génération de rapports PDF avec contrôle d'accès par rôle

Permissions:
- Admin Général: Tous les rapports
- Direction: Tous les rapports (lecture seule)
- Comptable: Rapports financiers + présences (salaires)
- Admin Chantier: Rapports de ses chantiers
- Chef Chantier: Rapports de son chantier (sauf budget global)
- Magasinier: ❌ Pas d'accès aux rapports
- Ouvrier: ❌ Pas d'accès aux rapports
- Client: ❌ Pas d'accès aux rapports internes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime
from calendar import monthrange
from io import BytesIO
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect

from app.core.database import get_db
from app.core.security import get_current_user, RoleEnum, has_chantier_access
from app.core.permissions import (
    require_permission,
    require_admin,
    has_permission
)
from app.models.chantier import Chantier
from app.models.depense import Depense
from app.models.employe import Employe, Presence
from app.models.materiel import Materiel

router = APIRouter(prefix="/rapports", tags=["Rapports"])


# =============================================================================
# FONCTIONS UTILITAIRES POUR PDF
# =============================================================================

def create_header(elements, styles, title, subtitle=""):
    """Créer un en-tête professionnel pour les rapports"""
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Barre de couleur
    d = Drawing(500, 5)
    d.add(Rect(0, 0, 500, 5, fillColor=colors.HexColor('#2196f3'), strokeColor=None))
    
    elements.append(Paragraph("🏗️ NEXUS GROUP", header_style))
    elements.append(Paragraph("Construction & Bâtiment - Dakar, Sénégal", subtitle_style))
    elements.append(d)
    elements.append(Spacer(1, 0.5*cm))
    
    # Titre du rapport
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#333333'),
        alignment=TA_CENTER,
        spaceAfter=5
    )
    elements.append(Paragraph(title, title_style))
    if subtitle:
        elements.append(Paragraph(subtitle, subtitle_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Date de génération
    date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=TA_RIGHT)
    elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
    elements.append(Spacer(1, 0.5*cm))


def create_styled_table(data, col_widths):
    """Créer un tableau stylisé"""
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196f3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def create_footer(elements, styles, confidential=False):
    """Créer le pied de page"""
    elements.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph("─" * 80, footer_style))
    
    if confidential:
        elements.append(Paragraph("NEXUS GROUP - Rapport confidentiel - Usage interne uniquement", footer_style))
    else:
        elements.append(Paragraph("NEXUS GROUP - Construction & Bâtiment | Dakar, Sénégal | contact@nexusgroup.sn | +221 77 123 45 67", footer_style))


# =============================================================================
# RAPPORT DE CHANTIER
# =============================================================================

@router.get("/chantier/{chantier_id}/pdf")
async def rapport_chantier_pdf(
    chantier_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_rapports"))
):
    """
    Rapport complet d'un chantier en PDF
    
    Permissions:
    - Admin, Direction: Tous les chantiers
    - Admin Chantier, Chef Chantier: Leurs chantiers
    
    ⚠️ Le budget est masqué pour certains rôles
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Récupérer le chantier
    result = await db.execute(select(Chantier).where(Chantier.id == chantier_id))
    chantier = result.scalar_one_or_none()
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chantier non trouvé"
        )
    
    # Vérifier l'accès au chantier
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, RoleEnum.COMPTABLE]:
        if not has_chantier_access(user, chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès aux rapports de ce chantier"
            )
    
    # Vérifier si l'utilisateur peut voir les budgets
    can_view_budget = has_permission(role, "view_budget") or role in [
        RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE, RoleEnum.DIRECTION
    ]
    
    # Récupérer les données
    depenses = (await db.execute(select(Depense).where(Depense.chantier_id == chantier_id))).scalars().all()
    employes = (await db.execute(select(Employe).where(Employe.chantier_id == chantier_id))).scalars().all()
    materiels = (await db.execute(select(Materiel).where(Materiel.chantier_id == chantier_id))).scalars().all()
    
    # Générer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # En-tête
    create_header(elements, styles, f"Rapport de Chantier", f"{chantier.nom} - {chantier.reference}")
    
    # Section: Informations générales
    section_style = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=14, textColor=colors.HexColor('#2196f3'), spaceBefore=15, spaceAfter=10)
    elements.append(Paragraph("📋 Informations Générales", section_style))
    
    # Construire les infos selon les permissions
    if can_view_budget:
        info_data = [
            ["Référence", chantier.reference, "Status", chantier.status.upper() if chantier.status else "-"],
            ["Client", chantier.client_nom or "-", "Téléphone", chantier.client_telephone or "-"],
            ["Adresse", f"{chantier.adresse or ''}, {chantier.ville or ''}", "Progression", f"{chantier.progression or 0}%"],
            ["Budget Prévu", f"{chantier.budget_prevu or 0:,.0f} FCFA", "Consommé", f"{chantier.budget_consomme or 0:,.0f} FCFA"],
        ]
    else:
        # Sans budget
        info_data = [
            ["Référence", chantier.reference, "Status", chantier.status.upper() if chantier.status else "-"],
            ["Client", chantier.client_nom or "-", "Téléphone", chantier.client_telephone or "-"],
            ["Adresse", f"{chantier.adresse or ''}, {chantier.ville or ''}", "Progression", f"{chantier.progression or 0}%"],
        ]
    
    info_table = Table(info_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e3f2fd')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(info_table)
    
    # Barre de progression budget (si autorisé)
    if can_view_budget and chantier.budget_prevu:
        reste = (chantier.budget_prevu or 0) - (chantier.budget_consomme or 0)
        pct = ((chantier.budget_consomme or 0) / chantier.budget_prevu * 100) if chantier.budget_prevu > 0 else 0
        
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(f"<b>Budget restant:</b> {reste:,.0f} FCFA ({100-pct:.1f}%)", styles['Normal']))
    
    # Section: Dépenses (si autorisé)
    if can_view_budget:
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"💰 Dépenses ({len(depenses)})", section_style))
        
        if depenses:
            dep_data = [["Référence", "Libellé", "Catégorie", "Montant", "Status"]]
            for d in depenses[:10]:  # Limiter à 10
                dep_data.append([
                    d.reference or "-",
                    (d.libelle or "")[:25],
                    d.categorie or "-",
                    f"{d.montant or 0:,.0f}",
                    d.status or "-"
                ])
            total_dep = sum(d.montant or 0 for d in depenses)
            dep_data.append(["", "", "TOTAL", f"{total_dep:,.0f} FCFA", ""])
            elements.append(create_styled_table(dep_data, [2.5*cm, 5*cm, 2.5*cm, 3*cm, 2.5*cm]))
        else:
            elements.append(Paragraph("Aucune dépense enregistrée", styles['Normal']))
    
    # Section: Employés (masquer salaires si pas autorisé)
    can_view_salaires = has_permission(role, "view_salaires")
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"👷 Équipe ({len(employes)})", section_style))
    
    if employes:
        if can_view_salaires:
            emp_data = [["Matricule", "Nom Complet", "Poste", "Salaire/Jour"]]
            total_salaire = 0
            for e in employes:
                emp_data.append([
                    e.matricule or "-",
                    f"{e.prenom or ''} {e.nom or ''}",
                    e.poste or "-",
                    f"{e.salaire_journalier or 0:,.0f}"
                ])
                total_salaire += e.salaire_journalier or 0
            emp_data.append(["", "", "TOTAL/JOUR", f"{total_salaire:,.0f} FCFA"])
            elements.append(create_styled_table(emp_data, [3*cm, 5*cm, 3.5*cm, 3.5*cm]))
        else:
            # Sans salaires
            emp_data = [["Matricule", "Nom Complet", "Poste"]]
            for e in employes:
                emp_data.append([
                    e.matricule or "-",
                    f"{e.prenom or ''} {e.nom or ''}",
                    e.poste or "-"
                ])
            elements.append(create_styled_table(emp_data, [4*cm, 6*cm, 5*cm]))
    else:
        elements.append(Paragraph("Aucun employé assigné", styles['Normal']))
    
    # Section: Stock
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"📦 Stock Matériels ({len(materiels)})", section_style))
    
    if materiels:
        mat_data = [["Nom", "Catégorie", "Qté", "Unité", "Alerte"]]
        for m in materiels:
            alerte = "⚠️ OUI" if (m.quantite or 0) <= (m.seuil_alerte or 0) else "Non"
            mat_data.append([
                (m.nom or "")[:20],
                m.categorie or "-",
                f"{m.quantite or 0}",
                m.unite or "-",
                alerte
            ])
        elements.append(create_styled_table(mat_data, [5*cm, 3*cm, 2*cm, 2*cm, 2*cm]))
    else:
        elements.append(Paragraph("Aucun matériel enregistré", styles['Normal']))
    
    # Footer
    create_footer(elements, styles)
    
    doc.build(elements)
    buffer.seek(0)
    
    # TODO: Logger pour audit
    # await log_audit(db, user, "export_rapport_chantier", chantier_id)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=rapport_{chantier.reference}.pdf"}
    )


# =============================================================================
# RAPPORT DE PRÉSENCES / SALAIRES
# =============================================================================

@router.get("/presences/{chantier_id}/pdf")
async def rapport_presences_pdf(
    chantier_id: int,
    mois: int = Query(..., ge=1, le=12),
    annee: int = Query(..., ge=2020, le=2100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_salaires"))
):
    """
    Rapport des présences et salaires en PDF
    
    ⚠️ SÉCURITÉ: Réservé aux rôles avec permission "view_salaires"
    - Admin Général
    - Comptable
    - Direction (lecture seule)
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Récupérer le chantier
    result = await db.execute(select(Chantier).where(Chantier.id == chantier_id))
    chantier = result.scalar_one_or_none()
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chantier non trouvé"
        )
    
    debut = date(annee, mois, 1)
    fin = date(annee, mois, monthrange(annee, mois)[1])
    
    employes = (await db.execute(select(Employe).where(Employe.chantier_id == chantier_id))).scalars().all()
    presences = (await db.execute(
        select(Presence).where(
            Presence.chantier_id == chantier_id,
            Presence.date >= debut,
            Presence.date <= fin
        )
    )).scalars().all()
    
    # Générer PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    mois_noms = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    create_header(elements, styles, "Rapport de Présences", f"{mois_noms[mois]} {annee} - {chantier.nom}")
    
    section_style = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=14, textColor=colors.HexColor('#4caf50'), spaceBefore=15, spaceAfter=10)
    elements.append(Paragraph("📋 Récapitulatif des Présences", section_style))
    
    # Tableau
    data = [["Matricule", "Nom Complet", "Poste", "Jours", "Heures", "Salaire/J", "Total Dû"]]
    total_salaires = 0
    total_jours = 0
    
    for emp in employes:
        emp_presences = [p for p in presences if p.employe_id == emp.id and p.status == "present"]
        jours = len(emp_presences)
        heures = sum(p.heures_travaillees or 0 for p in emp_presences)
        salaire_du = jours * (emp.salaire_journalier or 0)
        total_salaires += salaire_du
        total_jours += jours
        
        data.append([
            emp.matricule or "-",
            f"{emp.prenom or ''} {emp.nom or ''}",
            emp.poste or "-",
            str(jours),
            str(int(heures)),
            f"{emp.salaire_journalier or 0:,.0f}",
            f"{salaire_du:,.0f}"
        ])
    
    # Ligne total
    data.append(["", "TOTAL", "", str(total_jours), "", "", f"{total_salaires:,.0f} FCFA"])
    
    elements.append(create_styled_table(data, [2.5*cm, 4*cm, 2.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 3*cm]))
    
    # Résumé
    elements.append(Spacer(1, 0.5*cm))
    summary_style = ParagraphStyle('Summary', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#333'))
    elements.append(Paragraph(f"<b>💰 TOTAL SALAIRES À PAYER: {total_salaires:,.0f} FCFA</b>", summary_style))
    
    # Généré par
    elements.append(Spacer(1, 0.3*cm))
    generated_style = ParagraphStyle('Generated', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
    elements.append(Paragraph(f"Rapport généré par: {user.get('email', 'N/A')}", generated_style))
    
    # Footer
    create_footer(elements, styles, confidential=True)
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=presences_{chantier.reference}_{mois}_{annee}.pdf"}
    )


# =============================================================================
# RAPPORT FINANCIER GLOBAL
# =============================================================================

@router.get("/financier/pdf")
async def rapport_financier_global(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_rapports_financiers"))
):
    """
    Rapport financier global de tous les chantiers
    
    ⚠️ SÉCURITÉ: Réservé aux rôles avec permission "view_rapports_financiers"
    - Admin Général
    - Comptable
    - Direction (lecture seule)
    """
    
    chantiers = (await db.execute(select(Chantier))).scalars().all()
    depenses = (await db.execute(select(Depense))).scalars().all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    create_header(elements, styles, "Rapport Financier Global", f"Tous les chantiers")
    
    section_style = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=14, textColor=colors.HexColor('#ff9800'), spaceBefore=15, spaceAfter=10)
    
    # Résumé global
    elements.append(Paragraph("📊 Vue d'ensemble", section_style))
    
    total_budget = sum(c.budget_prevu or 0 for c in chantiers)
    total_consomme = sum(c.budget_consomme or 0 for c in chantiers)
    total_depenses = sum(d.montant or 0 for d in depenses)
    
    summary_data = [
        ["Indicateur", "Valeur"],
        ["Nombre de chantiers", str(len(chantiers))],
        ["Budget total prévu", f"{total_budget:,.0f} FCFA"],
        ["Budget consommé", f"{total_consomme:,.0f} FCFA"],
        ["Total dépenses", f"{total_depenses:,.0f} FCFA"],
        ["Reste à dépenser", f"{total_budget - total_consomme:,.0f} FCFA"],
    ]
    elements.append(create_styled_table(summary_data, [8*cm, 8*cm]))
    
    # Détail par chantier
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("🏗️ Détail par Chantier", section_style))
    
    chantier_data = [["Chantier", "Budget", "Consommé", "Reste", "%"]]
    for c in chantiers:
        reste = (c.budget_prevu or 0) - (c.budget_consomme or 0)
        pct = ((c.budget_consomme or 0) / c.budget_prevu * 100) if c.budget_prevu else 0
        chantier_data.append([
            (c.nom or "")[:20],
            f"{c.budget_prevu or 0:,.0f}",
            f"{c.budget_consomme or 0:,.0f}",
            f"{reste:,.0f}",
            f"{pct:.1f}%"
        ])
    
    elements.append(create_styled_table(chantier_data, [5*cm, 3*cm, 3*cm, 3*cm, 2*cm]))
    
    # Dépenses par catégorie
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("💰 Dépenses par Catégorie", section_style))
    
    categories = {}
    for d in depenses:
        cat = d.categorie or "Autre"
        categories[cat] = categories.get(cat, 0) + (d.montant or 0)
    
    cat_data = [["Catégorie", "Montant", "%"]]
    for cat, montant in sorted(categories.items(), key=lambda x: -x[1]):
        pct = (montant / total_depenses * 100) if total_depenses > 0 else 0
        cat_data.append([cat.upper(), f"{montant:,.0f} FCFA", f"{pct:.1f}%"])
    
    elements.append(create_styled_table(cat_data, [6*cm, 5*cm, 3*cm]))
    
    # Généré par
    elements.append(Spacer(1, 0.3*cm))
    generated_style = ParagraphStyle('Generated', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
    elements.append(Paragraph(f"Rapport généré par: {user.get('email', 'N/A')}", generated_style))
    
    # Footer confidentiel
    create_footer(elements, styles, confidential=True)
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=rapport_financier_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


# =============================================================================
# RAPPORT STOCK
# =============================================================================

@router.get("/stock/pdf")
async def rapport_stock_pdf(
    chantier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_stock"))
):
    """
    Rapport de stock en PDF
    
    Permissions:
    - Admin, Magasinier, Direction: Tous les chantiers
    - Chef Chantier: Son chantier
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    query = select(Materiel)
    
    if chantier_id:
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.MAGASINIER, RoleEnum.DIRECTION]:
            if not has_chantier_access(user, chantier_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce chantier"
                )
        query = query.where(Materiel.chantier_id == chantier_id)
    
    materiels = (await db.execute(query)).scalars().all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    titre = "Rapport de Stock"
    if chantier_id:
        result = await db.execute(select(Chantier).where(Chantier.id == chantier_id))
        chantier = result.scalar_one_or_none()
        titre = f"Rapport de Stock - {chantier.nom if chantier else ''}"
    
    create_header(elements, styles, titre, "État des stocks et alertes")
    
    section_style = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=14, textColor=colors.HexColor('#9c27b0'), spaceBefore=15, spaceAfter=10)
    
    # Alertes
    alertes = [m for m in materiels if (m.quantite or 0) <= (m.seuil_alerte or 0)]
    if alertes:
        elements.append(Paragraph(f"⚠️ Alertes Stock ({len(alertes)} articles)", section_style))
        alerte_data = [["Nom", "Chantier", "Qté", "Seuil", "Manque"]]
        for m in alertes:
            manque = (m.seuil_alerte or 0) - (m.quantite or 0)
            alerte_data.append([
                (m.nom or "")[:25],
                str(m.chantier_id),
                f"{m.quantite or 0}",
                f"{m.seuil_alerte or 0}",
                f"{max(0, manque)}"
            ])
        elements.append(create_styled_table(alerte_data, [6*cm, 2*cm, 2*cm, 2*cm, 2*cm]))
        elements.append(Spacer(1, 0.5*cm))
    
    # Liste complète
    elements.append(Paragraph(f"📦 Inventaire Complet ({len(materiels)} articles)", section_style))
    
    if materiels:
        mat_data = [["Nom", "Catégorie", "Qté", "Unité", "P.U.", "Valeur"]]
        total_valeur = 0
        for m in materiels:
            valeur = (m.quantite or 0) * (m.prix_unitaire or 0)
            total_valeur += valeur
            mat_data.append([
                (m.nom or "")[:20],
                m.categorie or "-",
                f"{m.quantite or 0}",
                m.unite or "-",
                f"{m.prix_unitaire or 0:,.0f}",
                f"{valeur:,.0f}"
            ])
        mat_data.append(["", "", "", "", "TOTAL", f"{total_valeur:,.0f} FCFA"])
        elements.append(create_styled_table(mat_data, [5*cm, 2.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 3*cm]))
    else:
        elements.append(Paragraph("Aucun matériel enregistré", styles['Normal']))
    
    create_footer(elements, styles)
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=rapport_stock_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


# =============================================================================
# LISTE DES RAPPORTS DISPONIBLES
# =============================================================================

@router.get("/")
async def list_rapports_disponibles(
    user: dict = Depends(get_current_user)
):
    """
    Liste des rapports disponibles selon le rôle de l'utilisateur
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    rapports = []
    
    # Rapport chantier
    if has_permission(role, "view_rapports"):
        rapports.append({
            "id": "chantier",
            "nom": "Rapport de Chantier",
            "description": "Rapport complet d'un chantier (infos, dépenses, équipe, stock)",
            "url": "/rapports/chantier/{chantier_id}/pdf",
            "params": ["chantier_id"]
        })
    
    # Rapport présences
    if has_permission(role, "view_salaires"):
        rapports.append({
            "id": "presences",
            "nom": "Rapport de Présences",
            "description": "Récapitulatif des présences et salaires par mois",
            "url": "/rapports/presences/{chantier_id}/pdf",
            "params": ["chantier_id", "mois", "annee"]
        })
    
    # Rapport financier global
    if has_permission(role, "view_rapports_financiers"):
        rapports.append({
            "id": "financier",
            "nom": "Rapport Financier Global",
            "description": "Vue d'ensemble financière de tous les chantiers",
            "url": "/rapports/financier/pdf",
            "params": []
        })
    
    # Rapport stock
    if has_permission(role, "view_stock"):
        rapports.append({
            "id": "stock",
            "nom": "Rapport de Stock",
            "description": "État des stocks et alertes",
            "url": "/rapports/stock/pdf",
            "params": ["chantier_id (optionnel)"]
        })
    
    return {
        "role": role,
        "rapports_disponibles": rapports
    }
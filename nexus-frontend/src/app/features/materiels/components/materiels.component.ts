import { Component, OnInit } from '@angular/core';
import { MaterielService, ChantierService } from '../../../core/services';
import { Materiel, CreateMateriel, CreateMouvement, Chantier } from '../../../core/models';

@Component({
  selector: 'app-materiels',
  templateUrl: './materiels.component.html',
  styleUrls: ['./materiels.component.scss']
})
export class MaterielsComponent implements OnInit {
  materiels: Materiel[] = [];
  alertes: Materiel[] = [];
  chantiers: Chantier[] = [];
  isModalOpen = false;
  isMouvementModalOpen = false;
  isLoading = false;

  formData: CreateMateriel = {
    chantier_id: 0,
    nom: '',
    categorie: 'ciment',
    unite: 'sac',
    quantite: 0,
    prix_unitaire: 0
  };

  mouvementData: CreateMouvement = {
    materiel_id: 0,
    type_mouvement: 'entree',
    quantite: 0,
    motif: ''
  };

  categories = [
    { value: 'ciment', label: 'Ciment' },
    { value: 'fer', label: 'Fer' },
    { value: 'agregat', label: 'Agrégats' },
    { value: 'bois', label: 'Bois' },
    { value: 'autres', label: 'Autres' }
  ];

  unites = [
    { value: 'sac', label: 'Sac' },
    { value: 'barre', label: 'Barre' },
    { value: 'm3', label: 'M³' },
    { value: 'kg', label: 'Kg' },
    { value: 'piece', label: 'Pièce' }
  ];

  constructor(
    private materielService: MaterielService,
    private chantierService: ChantierService
  ) {}

  ngOnInit(): void {
    this.loadMateriels();
    this.loadChantiers();
  }

  loadMateriels(): void {
    this.isLoading = true;
    this.materielService.getAll().subscribe({
      next: (data) => {
        this.materiels = data;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });

    this.materielService.getAlertes().subscribe({
      next: (data) => {
        this.alertes = data;
      }
    });
  }

  loadChantiers(): void {
    this.chantierService.getAll().subscribe({
      next: (data) => {
        this.chantiers = data;
      }
    });
  }

  openModal(): void {
    this.resetForm();
    this.isModalOpen = true;
  }

  closeModal(): void {
    this.isModalOpen = false;
  }

  openMouvementModal(materielId: number): void {
    this.mouvementData = {
      materiel_id: materielId,
      type_mouvement: 'entree',
      quantite: 0,
      motif: ''
    };
    this.isMouvementModalOpen = true;
  }

  closeMouvementModal(): void {
    this.isMouvementModalOpen = false;
  }

  resetForm(): void {
    this.formData = {
      chantier_id: 0,
      nom: '',
      categorie: 'ciment',
      unite: 'sac',
      quantite: 0,
      prix_unitaire: 0
    };
  }

  onSubmit(): void {
    if (!this.formData.chantier_id || !this.formData.nom) {
      return;
    }

    this.materielService.create(this.formData).subscribe({
      next: () => {
        this.closeModal();
        this.loadMateriels();
      }
    });
  }

  onMouvementSubmit(): void {
    if (!this.mouvementData.quantite) {
      return;
    }

    this.materielService.createMouvement(this.mouvementData).subscribe({
      next: () => {
        this.closeMouvementModal();
        this.loadMateriels();
      }
    });
  }

  isLowStock(materiel: Materiel): boolean {
    return materiel.quantite <= materiel.seuil_alerte;
  }

  getValeur(materiel: Materiel): number {
    return materiel.quantite * materiel.prix_unitaire;
  }
}

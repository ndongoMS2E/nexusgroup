import { Component, OnInit } from '@angular/core';
import { EmployeService, ChantierService } from '../../../core/services';
import { Chantier, PointageEmploye, CreatePointage } from '../../../core/models';

interface SalaireEmploye {
  employe_id: number;
  matricule: string;
  nom: string;
  prenom: string;
  poste: string;
  salaire_journalier: number;
  jours_travailles: number;
  heures_totales: number;
  salaire_periode: number;
}

@Component({
  selector: 'app-pointage',
  templateUrl: './pointage.component.html',
  styleUrls: ['./pointage.component.scss']
})
export class PointageComponent implements OnInit {
  chantiers: Chantier[] = [];
  pointages: PointageEmploye[] = [];
  
  selectedChantierId: number | null = null;
  selectedDate: string = '';
  isLoading = false;
  isSaving = false;

  // Salaires
  showSalaires = false;
  salairesData: SalaireEmploye[] = [];
  totalSalaires = 0;
  dateDebutSalaire: string = '';
  dateFinSalaire: string = '';
  isLoadingSalaires = false;

  constructor(
    private employeService: EmployeService,
    private chantierService: ChantierService
  ) {}

  ngOnInit(): void {
    this.selectedDate = new Date().toISOString().split('T')[0];
    
    // Période par défaut : mois en cours
    const now = new Date();
    this.dateDebutSalaire = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    this.dateFinSalaire = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
    
    this.loadChantiers();
  }

  loadChantiers(): void {
    this.chantierService.getAll().subscribe({
      next: (data) => {
        this.chantiers = data.sort((a, b) => a.id - b.id);
        if (this.chantiers.length > 0 && !this.selectedChantierId) {
          const chantierEnCours = this.chantiers.find(c => c.status === 'en_cours');
          this.selectedChantierId = chantierEnCours ? chantierEnCours.id : this.chantiers[0].id;
          this.loadPointage();
        }
      }
    });
  }

  loadPointage(): void {
    if (!this.selectedChantierId || !this.selectedDate) return;

    this.isLoading = true;
    this.employeService.getPointageJour(this.selectedChantierId, this.selectedDate).subscribe({
      next: (data) => {
        this.pointages = data;
        this.isLoading = false;
      },
      error: () => {
        this.pointages = [];
        this.isLoading = false;
      }
    });
  }

  onChantierChange(): void {
    this.loadPointage();
    if (this.showSalaires) {
      this.loadSalaires();
    }
  }

  onDateChange(): void {
    this.loadPointage();
  }

  setPresent(employe: PointageEmploye): void {
    employe.status = 'present';
  }

  setAbsent(employe: PointageEmploye): void {
    employe.status = 'absent';
  }

  sauvegarderPointage(): void {
    if (!this.selectedChantierId || !this.selectedDate || this.pointages.length === 0) {
      alert('Veuillez sélectionner un chantier et une date');
      return;
    }

    this.isSaving = true;
    const pointagesData: CreatePointage[] = this.pointages.map(p => ({
      employe_id: p.employe_id,
      chantier_id: this.selectedChantierId!,
      date: this.selectedDate,
      status: p.status === 'non_pointe' ? 'absent' : p.status,
      heures: p.heures || 8
    }));

    this.employeService.pointageMasse(this.selectedChantierId, this.selectedDate, pointagesData).subscribe({
      next: (response) => {
        this.isSaving = false;
        alert(response.message || 'Pointage enregistré avec succès !');
        this.loadPointage();
      },
      error: () => {
        this.isSaving = false;
        alert('Erreur lors de l\'enregistrement du pointage');
      }
    });
  }

  // ============ SALAIRES ============

  toggleSalaires(): void {
    this.showSalaires = !this.showSalaires;
    if (this.showSalaires) {
      this.loadSalaires();
    }
  }

  loadSalaires(): void {
    if (!this.selectedChantierId) return;

    this.isLoadingSalaires = true;
    this.employeService.calculerSalaires(
      this.selectedChantierId,
      this.dateDebutSalaire,
      this.dateFinSalaire
    ).subscribe({
      next: (data) => {
        this.salairesData = data.employes;
        this.totalSalaires = data.total_general;
        this.isLoadingSalaires = false;
      },
      error: () => {
        this.salairesData = [];
        this.totalSalaires = 0;
        this.isLoadingSalaires = false;
      }
    });
  }

  onPeriodeChange(): void {
    if (this.showSalaires) {
      this.loadSalaires();
    }
  }

  // Stats
  get totalEmployes(): number {
    return this.pointages.length;
  }

  get totalPresents(): number {
    return this.pointages.filter(p => p.status === 'present').length;
  }

  get totalAbsents(): number {
    return this.pointages.filter(p => p.status === 'absent').length;
  }

  get totalNonPointes(): number {
    return this.pointages.filter(p => p.status === 'non_pointe').length;
  }

  getChantierNom(): string {
    if (!this.selectedChantierId) return '';
    const chantier = this.chantiers.find(c => c.id === this.selectedChantierId);
    return chantier ? chantier.nom : '';
  }
}

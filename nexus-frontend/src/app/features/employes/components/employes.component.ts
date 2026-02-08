import { Component, OnInit } from '@angular/core';
import { EmployeService, ChantierService } from '../../../core/services';
import { Employe, CreateEmploye, Chantier } from '../../../core/models';

@Component({
  selector: 'app-employes',
  templateUrl: './employes.component.html',
  styleUrls: ['./employes.component.scss']
})
export class EmployesComponent implements OnInit {
  employes: Employe[] = [];
  filteredEmployes: Employe[] = [];
  chantiers: Chantier[] = [];
  
  isModalOpen = false;
  isAffectationModalOpen = false;
  isLoading = false;
  
  selectedEmploye: Employe | null = null;
  filterChantier: string = 'tous';
  searchTerm: string = '';

  formData: CreateEmploye = {
    nom: '',
    prenom: '',
    telephone: '',
    poste: 'manoeuvre',
    salaire_journalier: 0,
    date_embauche: '',
    chantier_id: undefined
  };

  affectationData = {
    chantier_id: null as number | null
  };

  postes = [
    { value: 'chef_equipe', label: "Chef d'équipe" },
    { value: 'macon', label: 'Maçon' },
    { value: 'ferrailleur', label: 'Ferrailleur' },
    { value: 'electricien', label: 'Électricien' },
    { value: 'plombier', label: 'Plombier' },
    { value: 'manoeuvre', label: 'Manoeuvre' }
  ];

  constructor(
    private employeService: EmployeService,
    private chantierService: ChantierService
  ) {}

  ngOnInit(): void {
    this.loadEmployes();
    this.loadChantiers();
  }

  loadEmployes(): void {
    this.isLoading = true;
    this.employeService.getAll().subscribe({
      next: (data) => {
        this.employes = data;
        this.applyFilters();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
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

  applyFilters(): void {
    let result = this.employes;

    // Filtre par chantier
    if (this.filterChantier === 'non_affectes') {
      result = result.filter(e => !e.chantier_id);
    } else if (this.filterChantier !== 'tous') {
      result = result.filter(e => e.chantier_id === parseInt(this.filterChantier));
    }

    // Filtre par recherche
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      result = result.filter(e =>
        e.nom.toLowerCase().includes(term) ||
        e.prenom.toLowerCase().includes(term) ||
        e.matricule.toLowerCase().includes(term)
      );
    }

    this.filteredEmployes = result;
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  onSearch(): void {
    this.applyFilters();
  }

  getChantierNom(chantierId: number | undefined): string {
    if (!chantierId) return 'Non affecté';
    const chantier = this.chantiers.find(c => c.id === chantierId);
    return chantier ? chantier.nom : 'Inconnu';
  }

  getPosteLabel(poste: string): string {
    const p = this.postes.find(p => p.value === poste);
    return p ? p.label : poste;
  }

  // Modal création
  openModal(): void {
    this.resetForm();
    this.isModalOpen = true;
  }

  closeModal(): void {
    this.isModalOpen = false;
  }

  resetForm(): void {
    const today = new Date().toISOString().split('T')[0];
    this.formData = {
      nom: '',
      prenom: '',
      telephone: '',
      poste: 'manoeuvre',
      salaire_journalier: 5000,
      date_embauche: today,
      chantier_id: undefined
    };
  }

  onSubmit(): void {
    if (!this.formData.nom || !this.formData.prenom || !this.formData.salaire_journalier) {
      return;
    }
    this.employeService.create(this.formData).subscribe({
      next: () => {
        this.closeModal();
        this.loadEmployes();
      }
    });
  }

  // Modal affectation
  openAffectationModal(employe: Employe): void {
    this.selectedEmploye = employe;
    this.affectationData.chantier_id = employe.chantier_id || null;
    this.isAffectationModalOpen = true;
  }

  closeAffectationModal(): void {
    this.isAffectationModalOpen = false;
    this.selectedEmploye = null;
  }

  confirmerAffectation(): void {
    if (!this.selectedEmploye) return;

    this.employeService.affecter(this.selectedEmploye.id, this.affectationData.chantier_id).subscribe({
      next: () => {
        this.closeAffectationModal();
        this.loadEmployes();
        alert('Affectation mise à jour avec succès !');
      },
      error: () => {
        alert('Erreur lors de l\'affectation');
      }
    });
  }

  deleteEmploye(id: number): void {
    if (confirm('Êtes-vous sûr de vouloir désactiver cet employé ?')) {
      this.employeService.delete(id).subscribe({
        next: () => this.loadEmployes()
      });
    }
  }

  // Stats
  get totalEmployes(): number {
    return this.employes.length;
  }

  get employesAffectes(): number {
    return this.employes.filter(e => e.chantier_id).length;
  }

  get employesNonAffectes(): number {
    return this.employes.filter(e => !e.chantier_id).length;
  }
}

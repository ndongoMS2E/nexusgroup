import { Component, OnInit } from '@angular/core';
import { ChantierService } from '../../../core/services';
import { Chantier, CreateChantier } from '../../../core/models';

interface StatusCount {
  status: string;
  label: string;
  icon: string;
  count: number;
}

@Component({
  selector: 'app-chantiers',
  templateUrl: './chantiers.component.html',
  styleUrls: ['./chantiers.component.scss']
})
export class ChantiersComponent implements OnInit {
  chantiers: Chantier[] = [];
  filteredChantiers: Chantier[] = [];
  selectedChantier: Chantier | null = null;
  
  isModalOpen = false;
  isDetailsModalOpen = false;
  isStatusModalOpen = false;
  isLoading = false;
  
  currentFilter = 'tous';
  searchTerm = '';
  
  statusCounts: StatusCount[] = [
    { status: 'tous', label: 'Tous', icon: '📋', count: 0 },
    { status: 'planifie', label: 'Planifiés', icon: '📝', count: 0 },
    { status: 'en_cours', label: 'En cours', icon: '🔄', count: 0 },
    { status: 'suspendu', label: 'Suspendus', icon: '⏸️', count: 0 },
    { status: 'termine', label: 'Terminés', icon: '✅', count: 0 }
  ];

  formData: CreateChantier = {
    nom: '',
    adresse: '',
    ville: 'Dakar',
    client_nom: '',
    budget_prevu: 0,
    date_debut: '',
    date_fin_prevue: ''
  };

  statusChangeData = {
    newStatus: '',
    raison: '',
    dateEffective: '',
    notifyChef: true,
    notifyClient: true,
    notifyEquipe: false
  };

  statusLabels: { [key: string]: { label: string; icon: string } } = {
    'planifie': { label: 'Planifié', icon: '📝' },
    'en_cours': { label: 'En Cours', icon: '🔄' },
    'suspendu': { label: 'Suspendu', icon: '⏸️' },
    'termine': { label: 'Terminé', icon: '✅' }
  };

  constructor(private chantierService: ChantierService) {}

  ngOnInit(): void {
    this.loadChantiers();
  }

  loadChantiers(): void {
    this.isLoading = true;
    this.chantierService.getAll().subscribe({
      next: (data) => {
        this.chantiers = data;
        this.updateStatusCounts();
        this.applyFilter();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  updateStatusCounts(): void {
    this.statusCounts[0].count = this.chantiers.length;
    this.statusCounts[1].count = this.chantiers.filter(c => c.status === 'planifie').length;
    this.statusCounts[2].count = this.chantiers.filter(c => c.status === 'en_cours').length;
    this.statusCounts[3].count = this.chantiers.filter(c => c.status === 'suspendu').length;
    this.statusCounts[4].count = this.chantiers.filter(c => c.status === 'termine').length;
  }

  applyFilter(): void {
    let result = this.chantiers;
    
    if (this.currentFilter !== 'tous') {
      result = result.filter(c => c.status === this.currentFilter);
    }
    
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      result = result.filter(c => 
        c.nom.toLowerCase().includes(term) || 
        c.client_nom.toLowerCase().includes(term) ||
        c.adresse.toLowerCase().includes(term)
      );
    }
    
    this.filteredChantiers = result;
  }

  filterByStatus(status: string): void {
    this.currentFilter = status;
    this.applyFilter();
  }

  onSearch(): void {
    this.applyFilter();
  }

  getProgressPercentage(chantier: Chantier): number {
    if (chantier.budget_prevu === 0) return 0;
    return Math.min(100, Math.round((chantier.budget_consomme / chantier.budget_prevu) * 100));
  }

  getStatusClass(status: string): string {
    return `status-${status.replace('_', '-')}`;
  }

  // Modal Nouveau Chantier
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
      adresse: '',
      ville: 'Dakar',
      client_nom: '',
      budget_prevu: 0,
      date_debut: today,
      date_fin_prevue: ''
    };
  }

  onSubmit(): void {
    if (!this.formData.nom || !this.formData.adresse || !this.formData.client_nom) {
      return;
    }

    this.chantierService.create(this.formData).subscribe({
      next: () => {
        this.closeModal();
        this.loadChantiers();
      }
    });
  }

  // Modal Détails
  openDetailsModal(chantier: Chantier): void {
    this.selectedChantier = chantier;
    this.isDetailsModalOpen = true;
  }

  closeDetailsModal(): void {
    this.isDetailsModalOpen = false;
    this.selectedChantier = null;
  }

  // Modal Changement de Statut
  openStatusModal(chantier: Chantier, newStatus: string): void {
    this.selectedChantier = chantier;
    this.statusChangeData = {
      newStatus: newStatus,
      raison: '',
      dateEffective: new Date().toISOString().split('T')[0],
      notifyChef: true,
      notifyClient: true,
      notifyEquipe: false
    };
    this.isStatusModalOpen = true;
    this.isDetailsModalOpen = false;
  }

  closeStatusModal(): void {
    this.isStatusModalOpen = false;
  }

  confirmStatusChange(): void {
    if (!this.selectedChantier || !this.statusChangeData.raison) {
      alert('Veuillez indiquer la raison du changement');
      return;
    }

    this.chantierService.update(this.selectedChantier.id, {
      status: this.statusChangeData.newStatus as 'planifie' | 'en_cours' | 'termine' | 'suspendu'
    }).subscribe({
      next: () => {
        this.closeStatusModal();
        this.loadChantiers();
        alert('Statut changé avec succès !');
      },
      error: () => {
        alert('Erreur lors du changement de statut');
      }
    });
  }

  // Actions rapides
  demarrerChantier(chantier: Chantier): void {
    this.openStatusModal(chantier, 'en_cours');
  }

  suspendreChantier(chantier: Chantier): void {
    this.openStatusModal(chantier, 'suspendu');
  }

  terminerChantier(chantier: Chantier): void {
    this.openStatusModal(chantier, 'termine');
  }

  reprendreChantier(chantier: Chantier): void {
    this.openStatusModal(chantier, 'en_cours');
  }

  deleteChantier(id: number): void {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce chantier ?')) {
      this.chantierService.delete(id).subscribe({
        next: () => this.loadChantiers()
      });
    }
  }

  downloadRapport(id: number): void {
    this.chantierService.downloadRapport(id);
  }

  isWorkflowStepCompleted(chantier: Chantier, step: string): boolean {
    const order = ['planifie', 'en_cours', 'termine'];
    const currentIndex = order.indexOf(chantier.status);
    const stepIndex = order.indexOf(step);
    if (chantier.status === 'suspendu') {
      return step === 'planifie';
    }
    return stepIndex < currentIndex;
  }

  isWorkflowStepActive(chantier: Chantier, step: string): boolean {
    return chantier.status === step;
  }
}

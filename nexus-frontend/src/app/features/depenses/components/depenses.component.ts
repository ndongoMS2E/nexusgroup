import { Component, OnInit } from '@angular/core';
import { DepenseService, ChantierService } from '../../../core/services';
import { Depense, CreateDepense, Chantier } from '../../../core/models';

@Component({
  selector: 'app-depenses',
  templateUrl: './depenses.component.html',
  styleUrls: ['./depenses.component.scss']
})
export class DepensesComponent implements OnInit {
  depenses: Depense[] = [];
  chantiers: Chantier[] = [];
  isModalOpen = false;
  isLoading = false;

  formData: CreateDepense = {
    chantier_id: 0,
    libelle: '',
    categorie: 'materiel',
    montant: 0,
    date_depense: '',
    fournisseur: ''
  };

  categories = [
    { value: 'materiel', label: 'Matériel' },
    { value: 'main_oeuvre', label: "Main d'oeuvre" },
    { value: 'transport', label: 'Transport' },
    { value: 'autres', label: 'Autres' }
  ];

  constructor(
    private depenseService: DepenseService,
    private chantierService: ChantierService
  ) {}

  ngOnInit(): void {
    this.loadDepenses();
    this.loadChantiers();
  }

  loadDepenses(): void {
    this.isLoading = true;
    this.depenseService.getAll().subscribe({
      next: (data) => {
        this.depenses = data;
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
      chantier_id: 0,
      libelle: '',
      categorie: 'materiel',
      montant: 0,
      date_depense: today,
      fournisseur: ''
    };
  }

  onSubmit(): void {
    if (!this.formData.chantier_id || !this.formData.libelle || !this.formData.montant) {
      return;
    }

    this.depenseService.create(this.formData).subscribe({
      next: () => {
        this.closeModal();
        this.loadDepenses();
      }
    });
  }

  approveDepense(id: number): void {
    this.depenseService.approve(id).subscribe({
      next: () => this.loadDepenses()
    });
  }

  deleteDepense(id: number): void {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette dépense ?')) {
      this.depenseService.delete(id).subscribe({
        next: () => this.loadDepenses()
      });
    }
  }
}

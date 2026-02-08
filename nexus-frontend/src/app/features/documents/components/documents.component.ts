import { Component, OnInit } from '@angular/core';
import { DocumentService, ChantierService } from '../../../core/services';
import { Document, Chantier } from '../../../core/models';

@Component({
  selector: 'app-documents',
  templateUrl: './documents.component.html',
  styleUrls: ['./documents.component.scss']
})
export class DocumentsComponent implements OnInit {
  documents: Document[] = [];
  chantiers: Chantier[] = [];
  isModalOpen = false;
  isLoading = false;
  selectedFile: File | null = null;
  fileName = '';

  formData = {
    chantier_id: 0,
    type_document: 'photo',
    description: ''
  };

  types = [
    { value: 'photo', label: 'Photo' },
    { value: 'plan', label: 'Plan' },
    { value: 'facture', label: 'Facture' },
    { value: 'contrat', label: 'Contrat' },
    { value: 'rapport', label: 'Rapport' }
  ];

  constructor(
    private documentService: DocumentService,
    private chantierService: ChantierService
  ) {}

  ngOnInit(): void {
    this.loadDocuments();
    this.loadChantiers();
  }

  loadDocuments(): void {
    this.isLoading = true;
    this.documentService.getAll().subscribe({
      next: (data) => {
        this.documents = data;
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
    this.formData = {
      chantier_id: 0,
      type_document: 'photo',
      description: ''
    };
    this.selectedFile = null;
    this.fileName = '';
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
      this.fileName = this.selectedFile.name;
    }
  }

  onSubmit(): void {
    if (!this.formData.chantier_id || !this.selectedFile) {
      alert('Veuillez sélectionner un chantier et un fichier');
      return;
    }

    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('chantier_id', this.formData.chantier_id.toString());
    formData.append('type_document', this.formData.type_document);
    formData.append('description', this.formData.description);

    this.documentService.upload(formData).subscribe({
      next: () => {
        this.closeModal();
        this.loadDocuments();
      }
    });
  }

  downloadDocument(id: number): void {
    this.documentService.download(id);
  }

  deleteDocument(id: number): void {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) {
      this.documentService.delete(id).subscribe({
        next: () => this.loadDocuments()
      });
    }
  }

  getIcon(type: string): string {
    return this.documentService.getIcon(type);
  }

  formatSize(bytes: number): string {
    return (bytes / 1024).toFixed(1) + ' KB';
  }
}

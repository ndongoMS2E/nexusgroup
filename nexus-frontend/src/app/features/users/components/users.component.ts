import { Component, OnInit } from '@angular/core';
import { UsersService, User, Role, CreateUser } from '../users.service';
import { ChantierService } from '../../../core/services';
import { Chantier } from '../../../core/models';

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})
export class UsersComponent implements OnInit {
  users: User[] = [];
  roles: Role[] = [];
  chantiers: Chantier[] = [];
  
  filteredUsers: User[] = [];
  selectedRole: string = '';
  searchTerm: string = '';
  
  showModal: boolean = false;
  showEditModal: boolean = false;
  isLoading: boolean = false;
  isSaving: boolean = false;
  
  // Formulaire création
  newUser: CreateUser = {
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: 'ouvrier',
    chantier_id: undefined
  };
  
  // Formulaire édition
  editingUser: User | null = null;
  editRole: string = '';
  editChantierId: number | undefined;

  constructor(
    private usersService: UsersService,
    private chantierService: ChantierService
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.isLoading = true;
    
    this.usersService.getUsers().subscribe({
      next: (data) => {
        this.users = data;
        this.applyFilters();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
        alert('Erreur lors du chargement des utilisateurs');
      }
    });

    this.usersService.getRoles().subscribe({
      next: (data) => this.roles = data
    });

    this.chantierService.getAll().subscribe({
      next: (data) => this.chantiers = data
    });
  }

  applyFilters(): void {
    this.filteredUsers = this.users.filter(user => {
      const matchesRole = !this.selectedRole || user.role === this.selectedRole;
      const matchesSearch = !this.searchTerm || 
        user.email.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        user.first_name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        user.last_name.toLowerCase().includes(this.searchTerm.toLowerCase());
      return matchesRole && matchesSearch;
    });
  }

  getRoleInfo(roleCode: string): Role | undefined {
    return this.roles.find(r => r.code === roleCode);
  }

  getChantierNom(chantierId: number | undefined): string {
    if (!chantierId) return '-';
    const chantier = this.chantiers.find(c => c.id === chantierId);
    return chantier ? chantier.nom : '-';
  }

  // ========== CRÉATION ==========
  
  openCreateModal(): void {
    this.newUser = {
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      role: 'ouvrier',
      chantier_id: undefined
    };
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
  }

  createUser(): void {
    if (!this.newUser.email || !this.newUser.password || !this.newUser.first_name || !this.newUser.last_name) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }

    this.isSaving = true;
    this.usersService.createUser(this.newUser).subscribe({
      next: () => {
        this.isSaving = false;
        this.showModal = false;
        this.loadData();
        alert('Utilisateur créé avec succès !');
      },
      error: (err) => {
        this.isSaving = false;
        alert(err.error?.detail || 'Erreur lors de la création');
      }
    });
  }

  // ========== ÉDITION ==========

  openEditModal(user: User): void {
    this.editingUser = user;
    this.editRole = user.role;
    this.editChantierId = user.chantier_id;
    this.showEditModal = true;
  }

  closeEditModal(): void {
    this.showEditModal = false;
    this.editingUser = null;
  }

  saveUserRole(): void {
    if (!this.editingUser) return;

    this.isSaving = true;
    this.usersService.updateUserRole(this.editingUser.id, this.editRole, this.editChantierId).subscribe({
      next: () => {
        this.isSaving = false;
        this.showEditModal = false;
        this.loadData();
        alert('Utilisateur modifié avec succès !');
      },
      error: (err) => {
        this.isSaving = false;
        alert(err.error?.detail || 'Erreur lors de la modification');
      }
    });
  }

  // ========== ACTIVATION ==========

  toggleUserStatus(user: User): void {
    const action = user.is_active ? 'désactiver' : 'activer';
    if (!confirm(`Voulez-vous ${action} le compte de ${user.first_name} ${user.last_name} ?`)) {
      return;
    }

    const request = user.is_active 
      ? this.usersService.deactivateUser(user.id)
      : this.usersService.activateUser(user.id);

    request.subscribe({
      next: () => {
        this.loadData();
        alert(`Compte ${action} avec succès !`);
      },
      error: (err) => {
        alert(err.error?.detail || `Erreur lors de l'${action}ation`);
      }
    });
  }
  // ========== GETTERS POUR STATS ==========

  get activeUsersCount(): number {
    return this.users.filter(u => u.is_active).length;
  }

  get inactiveUsersCount(): number {
    return this.users.filter(u => !u.is_active).length;
  }
}

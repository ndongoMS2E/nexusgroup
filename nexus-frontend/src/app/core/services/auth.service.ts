import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, tap, map } from 'rxjs';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { User, LoginResponse } from '../models';

// =============================================================================
// ÉNUMÉRATION DES RÔLES (8 rôles)
// =============================================================================

export enum RoleEnum {
  ADMIN_GENERAL = 'admin_general',
  ADMIN_CHANTIER = 'admin_chantier',
  COMPTABLE = 'comptable',
  CHEF_CHANTIER = 'chef_chantier',
  MAGASINIER = 'magasinier',
  OUVRIER = 'ouvrier',
  CLIENT = 'client',
  DIRECTION = 'direction'
}

// =============================================================================
// INFORMATIONS DES RÔLES
// =============================================================================

export const ROLE_INFO: { [key: string]: { name: string; color: string; icon: string; level: number } } = {
  [RoleEnum.ADMIN_GENERAL]: {
    name: 'Administrateur Général',
    color: '#e53935',
    icon: '👑',
    level: 100
  },
  [RoleEnum.DIRECTION]: {
    name: 'Direction / Associé',
    color: '#8e24aa',
    icon: '🎯',
    level: 90
  },
  [RoleEnum.ADMIN_CHANTIER]: {
    name: 'Administrateur de Chantier',
    color: '#fb8c00',
    icon: '🏗️',
    level: 80
  },
  [RoleEnum.COMPTABLE]: {
    name: 'Comptable / Financier',
    color: '#43a047',
    icon: '💰',
    level: 70
  },
  [RoleEnum.CHEF_CHANTIER]: {
    name: 'Chef de Chantier',
    color: '#1e88e5',
    icon: '👷',
    level: 60
  },
  [RoleEnum.MAGASINIER]: {
    name: 'Magasinier',
    color: '#00acc1',
    icon: '📦',
    level: 50
  },
  [RoleEnum.OUVRIER]: {
    name: 'Ouvrier / Technicien',
    color: '#757575',
    icon: '🔧',
    level: 20
  },
  [RoleEnum.CLIENT]: {
    name: 'Client',
    color: '#5c6bc0',
    icon: '🏠',
    level: 10
  }
};

// =============================================================================
// PERMISSIONS PAR RÔLE
// =============================================================================

export const ROLE_PERMISSIONS: { [key: string]: string[] } = {
  [RoleEnum.ADMIN_GENERAL]: ['all'],
  
  [RoleEnum.ADMIN_CHANTIER]: [
    'view_chantiers', 'view_chantiers_assignes', 'edit_chantier',
    'view_taches', 'create_tache', 'edit_tache', 'assign_tache',
    'view_journal', 'create_journal',
    'view_documents', 'upload_document', 'delete_document', 'validate_document_client',
    'view_employes', 'view_presences', 'manage_presences',
    'view_budget_chantier',
    'view_depenses', 'create_depense', 'validate_commande_chantier',
    'view_stock', 'view_stock_chantier',
    'view_rapports', 'view_rapports_chantier',
    'view_notifications'
  ],
  
  [RoleEnum.COMPTABLE]: [
    'view_chantiers',
    'view_documents', 'view_documents_techniques',
    'view_employes', 'view_all_employes', 'view_salaires', 'view_presences',
    'view_budget', 'view_budget_global', 'view_previsions', 'export_budget',
    'view_depenses', 'view_all_depenses', 'create_depense',
    'view_paiements', 'create_paiement', 'manage_paiements',
    'view_factures', 'create_facture', 'manage_factures',
    'view_avances', 'manage_avances',
    'view_rapports', 'view_rapports_financiers', 'export_rapports',
    'view_notifications'
  ],
  
  [RoleEnum.CHEF_CHANTIER]: [
    'view_chantiers', 'view_chantiers_assignes',
    'view_taches', 'create_tache', 'edit_tache', 'update_avancement',
    'view_journal', 'create_journal', 'edit_journal',
    'view_documents', 'upload_document',
    'view_employes', 'view_presences', 'create_presence', 'manage_presences', 'pointer',
    'view_depenses', 'create_depense',
    'view_commandes', 'create_commande',
    'view_stock', 'view_stock_chantier', 'create_stock', 'mouvement_stock',
    'view_equipements', 'view_equipements_chantier', 'create_demande_equipement',
    'propose_modification',
    'view_rapports', 'view_rapports_chantier',
    'view_notifications'
  ],
  
  [RoleEnum.MAGASINIER]: [
    'view_stock', 'view_all_stock', 'create_stock', 'mouvement_stock',
    'receive_materiel', 'transfer_stock', 'view_historique_stock',
    'view_equipements', 'manage_equipements',
    'view_commandes',
    'view_notifications'
  ],
  
  [RoleEnum.OUVRIER]: [
    'view_taches', 'view_taches_assignees', 'update_avancement',
    'view_presence_personnelle', 'pointer',
    'view_notifications'
  ],
  
  [RoleEnum.CLIENT]: [
    'view_chantiers', 'view_chantier_propre',
    'view_documents', 'view_documents_valides',
    'view_avancement',
    'view_notifications'
  ],
  
  [RoleEnum.DIRECTION]: [
    'view_chantiers', 'view_all_chantiers',
    'view_taches',
    'view_journal',
    'view_documents',
    'view_employes', 'view_all_employes', 'view_salaires', 'view_presences', 'view_all_presences',
    'view_budget', 'view_budget_global', 'view_previsions',
    'view_depenses', 'view_all_depenses',
    'view_paiements',
    'view_factures',
    'view_commandes',
    'view_stock', 'view_all_stock', 'view_historique_stock',
    'view_equipements',
    'view_rapports', 'view_rapports_financiers', 'view_rapports_techniques', 'view_rapports_rh',
    'view_dashboard_global',
    'view_audit',
    'view_notifications'
  ]
};

// =============================================================================
// SERVICE D'AUTHENTIFICATION
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private permissionsSubject = new BehaviorSubject<string[]>([]);
  
  public currentUser$ = this.currentUserSubject.asObservable();
  public permissions$ = this.permissionsSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    this.loadStoredUser();
  }

  // ===========================================================================
  // AUTHENTIFICATION
  // ===========================================================================

  private loadStoredUser(): void {
    const token = this.getToken();
    if (token) {
      this.getCurrentUser().subscribe({
        error: () => this.logout()
      });
    }
  }

  login(email: string, password: string): Observable<LoginResponse> {
    const body = new URLSearchParams();
    body.set('username', email);
    body.set('password', password);

    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded'
    });

    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, body.toString(), { headers }).pipe(
      tap(response => {
        localStorage.setItem('token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        this.getCurrentUser().subscribe();
      })
    );
  }

  getCurrentUser(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/auth/me`).pipe(
      tap(user => {
        this.currentUserSubject.next(user);
        this.loadPermissions(user.role);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    this.currentUserSubject.next(null);
    this.permissionsSubject.next([]);
    this.router.navigate(['/login']);
  }

  refreshToken(): Observable<LoginResponse> {
    const refreshToken = localStorage.getItem('refresh_token');
    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/refresh`, { refresh_token: refreshToken }).pipe(
      tap(response => {
        localStorage.setItem('token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
      })
    );
  }

  // ===========================================================================
  // TOKENS
  // ===========================================================================

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // ===========================================================================
  // UTILISATEUR COURANT
  // ===========================================================================

  get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  getUserInitials(): string {
    const user = this.currentUserValue;
    if (user) {
      return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase();
    }
    return 'XX';
  }

  getUserFullName(): string {
    const user = this.currentUserValue;
    if (user) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim();
    }
    return '';
  }

  // ===========================================================================
  // RÔLES
  // ===========================================================================

  /**
   * Récupérer le rôle de l'utilisateur courant
   */
  getUserRole(): string {
    return this.currentUserValue?.role || RoleEnum.OUVRIER;
  }

  /**
   * Vérifier si l'utilisateur a un rôle spécifique
   */
  hasRole(role: string): boolean {
    return this.getUserRole() === role;
  }

  /**
   * Vérifier si l'utilisateur a l'un des rôles spécifiés
   */
  hasAnyRole(roles: string[]): boolean {
    return roles.includes(this.getUserRole());
  }

  /**
   * Vérifier si l'utilisateur est admin général
   */
  isAdmin(): boolean {
    return this.hasRole(RoleEnum.ADMIN_GENERAL);
  }

  /**
   * Vérifier si l'utilisateur est admin (général ou chantier)
   */
  isAnyAdmin(): boolean {
    return this.hasAnyRole([RoleEnum.ADMIN_GENERAL, RoleEnum.ADMIN_CHANTIER]);
  }

  /**
   * Vérifier si le rôle est en lecture seule (Direction)
   */
  isReadOnly(): boolean {
    return this.hasRole(RoleEnum.DIRECTION);
  }

  /**
   * Récupérer les informations du rôle
   */
  getRoleInfo(role?: string): { name: string; color: string; icon: string; level: number } {
    const r = role || this.getUserRole();
    return ROLE_INFO[r] || ROLE_INFO[RoleEnum.OUVRIER];
  }

  /**
   * Récupérer le nom affiché du rôle
   */
  getRoleName(role?: string): string {
    return this.getRoleInfo(role).name;
  }

  /**
   * Récupérer la couleur du rôle
   */
  getRoleColor(role?: string): string {
    return this.getRoleInfo(role).color;
  }

  /**
   * Récupérer l'icône du rôle
   */
  getRoleIcon(role?: string): string {
    return this.getRoleInfo(role).icon;
  }

  // ===========================================================================
  // PERMISSIONS
  // ===========================================================================

  /**
   * Charger les permissions du rôle
   */
  private loadPermissions(role: string): void {
    const permissions = ROLE_PERMISSIONS[role] || [];
    this.permissionsSubject.next(permissions);
  }

  /**
   * Récupérer les permissions actuelles
   */
  getPermissions(): string[] {
    return this.permissionsSubject.value;
  }

  /**
   * Vérifier si l'utilisateur a une permission
   */
  hasPermission(permission: string): boolean {
    const permissions = this.getPermissions();
    
    // Admin a toutes les permissions
    if (permissions.includes('all')) {
      return true;
    }
    
    return permissions.includes(permission);
  }

  /**
   * Vérifier si l'utilisateur a l'une des permissions
   */
  hasAnyPermission(permissions: string[]): boolean {
    return permissions.some(p => this.hasPermission(p));
  }

  /**
   * Vérifier si l'utilisateur a toutes les permissions
   */
  hasAllPermissions(permissions: string[]): boolean {
    return permissions.every(p => this.hasPermission(p));
  }

  // ===========================================================================
  // ACCÈS CHANTIER
  // ===========================================================================

  /**
   * Vérifier si l'utilisateur a accès à un chantier spécifique
   */
  hasChantierAccess(chantierId: number): boolean {
    const user = this.currentUserValue;
    if (!user) return false;

    const role = user.role;

    // Ces rôles ont accès à tous les chantiers
    if ([RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, RoleEnum.COMPTABLE, RoleEnum.MAGASINIER].includes(role as RoleEnum)) {
      return true;
    }

    // Vérifier les chantiers assignés
    const chantiersAssignes = user.chantiers_assignes || [];
    if (chantiersAssignes.includes(chantierId)) {
      return true;
    }

    // Vérifier le chantier principal
    if (user.chantier_id === chantierId) {
      return true;
    }

    return false;
  }

  /**
   * Récupérer les chantiers accessibles
   */
  getAccessibleChantiers(): number[] {
    const user = this.currentUserValue;
    if (!user) return [];

    // Admin, Direction, Comptable, Magasinier: tous les chantiers
    if ([RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, RoleEnum.COMPTABLE, RoleEnum.MAGASINIER].includes(user.role as RoleEnum)) {
      return []; // Retourne vide = tous
    }

    // Autres: chantiers assignés
    const chantiers = user.chantiers_assignes || [];
    if (user.chantier_id && !chantiers.includes(user.chantier_id)) {
      chantiers.push(user.chantier_id);
    }

    return chantiers;
  }

  // ===========================================================================
  // UTILITAIRES
  // ===========================================================================

  /**
   * Vérifier si l'utilisateur peut créer des utilisateurs
   */
  canCreateUser(): boolean {
    return this.isAdmin();
  }

  /**
   * Vérifier si l'utilisateur peut voir les salaires
   */
  canViewSalaires(): boolean {
    return this.hasPermission('view_salaires');
  }

  /**
   * Vérifier si l'utilisateur peut voir le budget global
   */
  canViewBudget(): boolean {
    return this.hasAnyPermission(['view_budget', 'view_budget_global', 'view_budget_chantier']);
  }

  /**
   * Vérifier si l'utilisateur peut approuver des dépenses
   */
  canApproveDepenses(): boolean {
    return this.isAdmin();
  }

  /**
   * Vérifier si l'utilisateur peut exporter des rapports
   */
  canExportRapports(): boolean {
    return this.hasPermission('export_rapports');
  }

  /**
   * Récupérer les permissions depuis l'API (optionnel)
   */
  fetchPermissionsFromApi(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/auth/me/permissions`).pipe(
      tap(response => {
        if (response.permissions) {
          this.permissionsSubject.next(response.permissions);
        }
      })
    );
  }
}
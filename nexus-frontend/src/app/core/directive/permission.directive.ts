import { Directive, Input, TemplateRef, ViewContainerRef, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { AuthService } from '../services/auth.service';

// =============================================================================
// DIRECTIVE *hasPermission
// =============================================================================

/**
 * Directive pour afficher/cacher un élément selon une permission
 * 
 * Usage:
 *   <button *hasPermission="'create_depense'">Créer</button>
 *   <div *hasPermission="'view_salaires'">Salaires: ...</div>
 */
@Directive({
  selector: '[hasPermission]'
})
export class HasPermissionDirective implements OnInit, OnDestroy {
  private permission: string = '';
  private subscription?: Subscription;

  @Input()
  set hasPermission(permission: string) {
    this.permission = permission;
    this.updateView();
  }

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Écouter les changements d'utilisateur
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (this.authService.hasPermission(this.permission)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// DIRECTIVE *hasAnyPermission
// =============================================================================

/**
 * Directive pour afficher si l'utilisateur a AU MOINS UNE des permissions
 * 
 * Usage:
 *   <div *hasAnyPermission="['view_budget', 'view_depenses']">Finances</div>
 */
@Directive({
  selector: '[hasAnyPermission]'
})
export class HasAnyPermissionDirective implements OnInit, OnDestroy {
  private permissions: string[] = [];
  private subscription?: Subscription;

  @Input()
  set hasAnyPermission(permissions: string[]) {
    this.permissions = permissions;
    this.updateView();
  }

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (this.authService.hasAnyPermission(this.permissions)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// DIRECTIVE *hasAllPermissions
// =============================================================================

/**
 * Directive pour afficher si l'utilisateur a TOUTES les permissions
 * 
 * Usage:
 *   <button *hasAllPermissions="['view_depenses', 'approve_depense']">Approuver</button>
 */
@Directive({
  selector: '[hasAllPermissions]'
})
export class HasAllPermissionsDirective implements OnInit, OnDestroy {
  private permissions: string[] = [];
  private subscription?: Subscription;

  @Input()
  set hasAllPermissions(permissions: string[]) {
    this.permissions = permissions;
    this.updateView();
  }

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (this.authService.hasAllPermissions(this.permissions)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// DIRECTIVE *hasRole
// =============================================================================

/**
 * Directive pour afficher/cacher un élément selon un rôle
 * 
 * Usage:
 *   <div *hasRole="'admin_general'">Section Admin</div>
 */
@Directive({
  selector: '[hasRole]'
})
export class HasRoleDirective implements OnInit, OnDestroy {
  private role: string = '';
  private subscription?: Subscription;

  @Input()
  set hasRole(role: string) {
    this.role = role;
    this.updateView();
  }

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (this.authService.hasRole(this.role)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// DIRECTIVE *hasAnyRole
// =============================================================================

/**
 * Directive pour afficher si l'utilisateur a AU MOINS UN des rôles
 * 
 * Usage:
 *   <div *hasAnyRole="['admin_general', 'comptable', 'direction']">Finances</div>
 */
@Directive({
  selector: '[hasAnyRole]'
})
export class HasAnyRoleDirective implements OnInit, OnDestroy {
  private roles: string[] = [];
  private subscription?: Subscription;

  @Input()
  set hasAnyRole(roles: string[]) {
    this.roles = roles;
    this.updateView();
  }

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (this.authService.hasAnyRole(this.roles)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// DIRECTIVE *isAdmin
// =============================================================================

/**
 * Directive pour afficher seulement si Admin Général
 * 
 * Usage:
 *   <button *isAdmin>Supprimer</button>
 */
@Directive({
  selector: '[isAdmin]'
})
export class IsAdminDirective implements OnInit, OnDestroy {
  private subscription?: Subscription;

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
    this.updateView();
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (this.authService.isAdmin()) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// DIRECTIVE *isNotReadOnly
// =============================================================================

/**
 * Directive pour cacher les éléments pour les rôles en lecture seule (Direction)
 * 
 * Usage:
 *   <button *isNotReadOnly>Modifier</button>
 */
@Directive({
  selector: '[isNotReadOnly]'
})
export class IsNotReadOnlyDirective implements OnInit, OnDestroy {
  private subscription?: Subscription;

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
    this.updateView();
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (!this.authService.isReadOnly()) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// DIRECTIVE *hasChantierAccess
// =============================================================================

/**
 * Directive pour afficher si l'utilisateur a accès à un chantier
 * 
 * Usage:
 *   <button *hasChantierAccess="chantierId">Voir détails</button>
 */
@Directive({
  selector: '[hasChantierAccess]'
})
export class HasChantierAccessDirective implements OnInit, OnDestroy {
  private chantierId: number = 0;
  private subscription?: Subscription;

  @Input()
  set hasChantierAccess(chantierId: number) {
    this.chantierId = chantierId;
    this.updateView();
  }

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.subscription = this.authService.currentUser$.subscribe(() => {
      this.updateView();
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  private updateView(): void {
    this.viewContainer.clear();
    
    if (this.authService.hasChantierAccess(this.chantierId)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
}

// =============================================================================
// MODULE DES DIRECTIVES
// =============================================================================

import { NgModule } from '@angular/core';

@NgModule({
  declarations: [
    HasPermissionDirective,
    HasAnyPermissionDirective,
    HasAllPermissionsDirective,
    HasRoleDirective,
    HasAnyRoleDirective,
    IsAdminDirective,
    IsNotReadOnlyDirective,
    HasChantierAccessDirective
  ],
  exports: [
    HasPermissionDirective,
    HasAnyPermissionDirective,
    HasAllPermissionsDirective,
    HasRoleDirective,
    HasAnyRoleDirective,
    IsAdminDirective,
    IsNotReadOnlyDirective,
    HasChantierAccessDirective
  ]
})
export class PermissionDirectivesModule {}
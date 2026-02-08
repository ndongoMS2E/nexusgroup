import { Injectable } from '@angular/core';
import { 
  CanActivate, 
  CanActivateChild,
  Router, 
  ActivatedRouteSnapshot, 
  RouterStateSnapshot,
  UrlTree
} from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService, RoleEnum } from '../services/auth.service';

// =============================================================================
// GUARD D'AUTHENTIFICATION DE BASE
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate, CanActivateChild {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean | UrlTree | Observable<boolean | UrlTree> {
    
    // Vérifier l'authentification
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login'], { 
        queryParams: { returnUrl: state.url } 
      });
      return false;
    }

    // Vérifier les rôles requis (si définis dans la route)
    const requiredRoles = route.data['roles'] as string[];
    if (requiredRoles && requiredRoles.length > 0) {
      if (!this.authService.hasAnyRole(requiredRoles)) {
        this.router.navigate(['/unauthorized']);
        return false;
      }
    }

    // Vérifier les permissions requises (si définies dans la route)
    const requiredPermissions = route.data['permissions'] as string[];
    if (requiredPermissions && requiredPermissions.length > 0) {
      const requireAll = route.data['requireAllPermissions'] ?? false;
      
      if (requireAll) {
        if (!this.authService.hasAllPermissions(requiredPermissions)) {
          this.router.navigate(['/unauthorized']);
          return false;
        }
      } else {
        if (!this.authService.hasAnyPermission(requiredPermissions)) {
          this.router.navigate(['/unauthorized']);
          return false;
        }
      }
    }

    // Vérifier l'accès au chantier (si défini dans la route)
    const chantierId = route.params['chantierId'] || route.params['id'];
    const requireChantierAccess = route.data['requireChantierAccess'] ?? false;
    if (requireChantierAccess && chantierId) {
      if (!this.authService.hasChantierAccess(Number(chantierId))) {
        this.router.navigate(['/unauthorized']);
        return false;
      }
    }

    return true;
  }

  canActivateChild(
    childRoute: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): boolean | UrlTree | Observable<boolean | UrlTree> {
    return this.canActivate(childRoute, state);
  }
}

// =============================================================================
// GUARD ADMIN UNIQUEMENT
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    if (!this.authService.isAdmin()) {
      this.router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  }
}

// =============================================================================
// GUARD ADMIN (GÉNÉRAL OU CHANTIER)
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class AnyAdminGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    if (!this.authService.isAnyAdmin()) {
      this.router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  }
}

// =============================================================================
// GUARD PAR RÔLE
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    const requiredRoles = route.data['roles'] as string[];
    
    if (!requiredRoles || requiredRoles.length === 0) {
      return true;
    }

    if (!this.authService.hasAnyRole(requiredRoles)) {
      this.router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  }
}

// =============================================================================
// GUARD PAR PERMISSION
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class PermissionGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    const requiredPermissions = route.data['permissions'] as string[];
    
    if (!requiredPermissions || requiredPermissions.length === 0) {
      return true;
    }

    const requireAll = route.data['requireAllPermissions'] ?? false;

    if (requireAll) {
      if (!this.authService.hasAllPermissions(requiredPermissions)) {
        this.router.navigate(['/unauthorized']);
        return false;
      }
    } else {
      if (!this.authService.hasAnyPermission(requiredPermissions)) {
        this.router.navigate(['/unauthorized']);
        return false;
      }
    }

    return true;
  }
}

// =============================================================================
// GUARD ACCÈS CHANTIER
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class ChantierAccessGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    // Récupérer l'ID du chantier depuis les paramètres
    const chantierId = route.params['chantierId'] || route.params['id'];
    
    if (!chantierId) {
      return true; // Pas de chantier spécifique demandé
    }

    if (!this.authService.hasChantierAccess(Number(chantierId))) {
      this.router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  }
}

// =============================================================================
// GUARD INTERDIT LECTURE SEULE (Direction)
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class NotReadOnlyGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    // Direction est en lecture seule, ne peut pas accéder aux pages de modification
    if (this.authService.isReadOnly()) {
      this.router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  }
}

// =============================================================================
// GUARD COMPTABLE / FINANCIER
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class FinanceGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    // Seuls Admin, Comptable et Direction peuvent voir les finances
    const allowedRoles = [
      RoleEnum.ADMIN_GENERAL,
      RoleEnum.COMPTABLE,
      RoleEnum.DIRECTION
    ];

    if (!this.authService.hasAnyRole(allowedRoles)) {
      this.router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  }
}

// =============================================================================
// GUARD STOCK / MAGASINIER
// =============================================================================

@Injectable({
  providedIn: 'root'
})
export class StockGuard implements CanActivate {
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot, 
    state: RouterStateSnapshot
  ): boolean {
    
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    if (!this.authService.hasPermission('view_stock')) {
      this.router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  }
}
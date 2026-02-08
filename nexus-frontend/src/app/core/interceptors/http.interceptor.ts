import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, filter, take, switchMap, finalize } from 'rxjs/operators';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

// =============================================================================
// INTERCEPTEUR JWT - Ajoute le token à toutes les requêtes
// =============================================================================

@Injectable()
export class JwtInterceptor implements HttpInterceptor {

  constructor(private authService: AuthService) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    
    // Récupérer le token
    const token = this.authService.getToken();
    
    // Si token existe, l'ajouter au header
    if (token) {
      request = this.addToken(request, token);
    }

    return next.handle(request);
  }

  private addToken(request: HttpRequest<any>, token: string): HttpRequest<any> {
    return request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }
}

// =============================================================================
// INTERCEPTEUR D'ERREURS - Gère les erreurs HTTP et le refresh token
// =============================================================================

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {

  private isRefreshing = false;
  private refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(null);

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    
    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        
        // Erreur 401 - Non autorisé
        if (error.status === 401) {
          return this.handle401Error(request, next);
        }
        
        // Erreur 403 - Interdit
        if (error.status === 403) {
          this.handle403Error(error);
        }
        
        // Erreur 404 - Non trouvé
        if (error.status === 404) {
          console.error('Ressource non trouvée:', error.url);
        }
        
        // Erreur 500 - Erreur serveur
        if (error.status >= 500) {
          console.error('Erreur serveur:', error.message);
        }

        return throwError(() => error);
      })
    );
  }

  /**
   * Gérer l'erreur 401 - Tenter de rafraîchir le token
   */
  private handle401Error(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    
    // Si c'est une requête de login ou refresh, ne pas intercepter
    if (request.url.includes('/auth/login') || request.url.includes('/auth/refresh')) {
      this.authService.logout();
      return throwError(() => new Error('Session expirée'));
    }

    // Si on est déjà en train de rafraîchir le token
    if (this.isRefreshing) {
      return this.refreshTokenSubject.pipe(
        filter(token => token != null),
        take(1),
        switchMap(token => {
          return next.handle(this.addTokenToRequest(request, token));
        })
      );
    }

    // Tenter de rafraîchir le token
    this.isRefreshing = true;
    this.refreshTokenSubject.next(null);

    const refreshToken = this.authService.getRefreshToken();

    if (refreshToken) {
      return this.authService.refreshToken().pipe(
        switchMap((response) => {
          this.isRefreshing = false;
          this.refreshTokenSubject.next(response.access_token);
          return next.handle(this.addTokenToRequest(request, response.access_token));
        }),
        catchError((err) => {
          this.isRefreshing = false;
          this.authService.logout();
          return throwError(() => err);
        }),
        finalize(() => {
          this.isRefreshing = false;
        })
      );
    } else {
      // Pas de refresh token, déconnecter
      this.authService.logout();
      return throwError(() => new Error('Session expirée'));
    }
  }

  /**
   * Gérer l'erreur 403 - Accès interdit
   */
  private handle403Error(error: HttpErrorResponse): void {
    console.error('Accès interdit:', error.message);
    
    // Optionnel: Rediriger vers une page "Non autorisé"
    // this.router.navigate(['/unauthorized']);
  }

  /**
   * Ajouter le token à une requête
   */
  private addTokenToRequest(request: HttpRequest<any>, token: string): HttpRequest<any> {
    return request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }
}

// =============================================================================
// INTERCEPTEUR DE CHARGEMENT (Optionnel)
// =============================================================================

@Injectable()
export class LoadingInterceptor implements HttpInterceptor {

  private activeRequests = 0;
  
  // Tu peux injecter un service de loading ici
  // constructor(private loadingService: LoadingService) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    
    // Ignorer certaines requêtes (ex: notifications)
    if (request.url.includes('/notifications')) {
      return next.handle(request);
    }

    this.activeRequests++;
    
    // Afficher le loader
    // this.loadingService.show();

    return next.handle(request).pipe(
      finalize(() => {
        this.activeRequests--;
        
        if (this.activeRequests === 0) {
          // Cacher le loader
          // this.loadingService.hide();
        }
      })
    );
  }
}

// =============================================================================
// CONFIGURATION DES INTERCEPTEURS
// =============================================================================

import { HTTP_INTERCEPTORS } from '@angular/common/http';

export const httpInterceptorProviders = [
  // L'ordre est important !
  
  // 1. Ajouter le token JWT
  { 
    provide: HTTP_INTERCEPTORS, 
    useClass: JwtInterceptor, 
    multi: true 
  },
  
  // 2. Gérer les erreurs et refresh token
  { 
    provide: HTTP_INTERCEPTORS, 
    useClass: ErrorInterceptor, 
    multi: true 
  },
  
  // 3. Loader (optionnel)
  // { 
  //   provide: HTTP_INTERCEPTORS, 
  //   useClass: LoadingInterceptor, 
  //   multi: true 
  // },
];
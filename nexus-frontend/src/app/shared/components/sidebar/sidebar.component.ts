import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

interface NavItem {
  icon: string;
  label: string;
  route: string;
  badge?: number;
  roles: string[];
}

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {
  currentRoute = '';
  notificationCount = 0;

  /*
  RÔLES ET ACCÈS SELON SPÉCIFICATIONS:
  =====================================
  1. admin_general     → Accès TOTAL
  2. admin_chantier    → Chantiers assignés, validation matériaux, documents chantier
  3. comptable         → Finance uniquement (budget, dépenses, paiements, factures)
  4. chef_chantier     → Terrain (tâches, journal, pointage, stock chantier, demandes)
  5. magasinier        → Stock uniquement (entrées/sorties, affectation, réception)
  6. ouvrier           → Très limité (tâches assignées, pointage personnel)
  7. client            → Consultatif (avancement, photos/docs validés)
  8. direction         → Lecture seule TOUT (supervision)
  */

  allNavItems: NavItem[] = [
    { 
      icon: '📊', 
      label: 'Dashboard', 
      route: '/dashboard',
      roles: ['admin_general', 'admin_chantier', 'comptable', 'chef_chantier', 'magasinier', 'ouvrier', 'client', 'direction']
    },
    { 
      icon: '🏗️', 
      label: 'Chantiers', 
      route: '/chantiers',
      // Admin, Admin chantier, Chef chantier, Direction (lecture), Client (son chantier)
      roles: ['admin_general', 'admin_chantier', 'chef_chantier', 'direction', 'client']
    },
    { 
      icon: '💰', 
      label: 'Dépenses', 
      route: '/depenses',
      // Admin, Comptable (gestion financière), Direction (lecture)
      roles: ['admin_general', 'comptable', 'direction']
    },
    { 
      icon: '👷', 
      label: 'Employés', 
      route: '/employes',
      // Admin, Admin chantier, Chef chantier (pointage), Comptable (paiements), Direction (lecture)
      // ⛔ Magasinier: pas d'accès RH
      // ⛔ Client: pas d'accès RH
      roles: ['admin_general', 'admin_chantier', 'chef_chantier', 'comptable', 'direction']
    },
    { 
      icon: '📋', 
      label: 'Pointage', 
      route: '/pointage',
      // Admin, Admin chantier, Chef chantier (pointage ouvriers), Comptable (paiements)
      // Ouvrier: pointage personnel uniquement (géré dans le composant)
      roles: ['admin_general', 'admin_chantier', 'chef_chantier', 'comptable', 'ouvrier']
    },
    { 
      icon: '📦', 
      label: 'Matériels', 
      route: '/materiels',
      // Admin, Admin chantier (validation), Chef chantier (stock chantier, demandes), Magasinier (gestion stock), Direction (lecture)
      // ⛔ Comptable: pas d'accès technique
      // ⛔ Client: pas d'accès
      roles: ['admin_general', 'admin_chantier', 'chef_chantier', 'magasinier', 'direction']
    },
    { 
      icon: '📁', 
      label: 'Documents', 
      route: '/documents',
      // Admin, Admin chantier, Chef chantier (upload), Comptable (lecture docs techniques), Direction (lecture), Client (docs validés)
      roles: ['admin_general', 'admin_chantier', 'chef_chantier', 'comptable', 'direction', 'client']
    },
    { 
      icon: '🔔', 
      label: 'Notifications', 
      route: '/notifications',
      // Tous les rôles
      roles: ['admin_general', 'admin_chantier', 'comptable', 'chef_chantier', 'magasinier', 'ouvrier', 'client', 'direction']
    },
    { 
      icon: '👥', 
      label: 'Utilisateurs', 
      route: '/users',
      // Admin uniquement (création/modification utilisateurs)
      roles: ['admin_general']
    }
  ];

  constructor(
    public authService: AuthService,
    private notificationService: NotificationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.currentRoute = event.url;
    });

    this.currentRoute = this.router.url;

    this.notificationService.count$.subscribe(count => {
      this.notificationCount = count;
    });

    this.notificationService.refreshCount();
  }

  get navItems(): NavItem[] {
    const user = this.authService.currentUserValue;
    const userRole = user?.role || '';
    
    return this.allNavItems.filter(item => {
      return item.roles.includes(userRole);
    });
  }

  isActive(route: string): boolean {
    return this.currentRoute.startsWith(route);
  }

  logout(): void {
    this.authService.logout();
  }
}

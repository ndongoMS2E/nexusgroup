import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from './core/guards/auth.guard';
import { LayoutComponent } from './shared/components/layout/layout.component';

const routes: Routes = [
  {
    path: 'login',
    loadChildren: () => import('./features/auth/auth.module').then(m => m.AuthModule)
  },
  {
    path: '',
    component: LayoutComponent,
    canActivate: [AuthGuard],
    children: [
      {
        path: 'dashboard',
        loadChildren: () => import('./features/dashboard/dashboard.module').then(m => m.DashboardModule)
      },
      {
        path: 'chantiers',
        loadChildren: () => import('./features/chantiers/chantiers.module').then(m => m.ChantiersModule)
      },
      {
        path: 'depenses',
        loadChildren: () => import('./features/depenses/depenses.module').then(m => m.DepensesModule)
      },
      {
        path: 'employes',
        loadChildren: () => import('./features/employes/employes.module').then(m => m.EmployesModule)
      },
      {
        path: 'pointage',
        loadChildren: () => import('./features/pointage/pointage.module').then(m => m.PointageModule)
      },
      {
        path: 'materiels',
        loadChildren: () => import('./features/materiels/materiels.module').then(m => m.MaterielsModule)
      },
      {
        path: 'documents',
        loadChildren: () => import('./features/documents/documents.module').then(m => m.DocumentsModule)
      },
      {
        path: 'notifications',
        loadChildren: () => import('./features/notifications/notifications.module').then(m => m.NotificationsModule)
      },
      {
        path: 'users',
        loadChildren: () => import('./features/users/users.module').then(m => m.UsersModule)
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}

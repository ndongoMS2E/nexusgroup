import { Component, OnInit } from '@angular/core';
import { forkJoin } from 'rxjs';
import { ChantierService, DepenseService, EmployeService, MaterielService } from '../../../core/services';
import { Chantier, Materiel } from '../../../core/models';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  stats = {
    chantiers: 0,
    employes: 0,
    depenses: 0,
    alertes: 0
  };

  recentChantiers: Chantier[] = [];
  alertes: Materiel[] = [];
  isLoading = true;

  constructor(
    private chantierService: ChantierService,
    private depenseService: DepenseService,
    private employeService: EmployeService,
    private materielService: MaterielService
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.isLoading = true;

    forkJoin({
      chantiers: this.chantierService.getAll(),
      depenses: this.depenseService.getAll(),
      employes: this.employeService.getAll(),
      alertes: this.materielService.getAlertes()
    }).subscribe({
      next: (data) => {
        this.stats.chantiers = data.chantiers.length;
        this.stats.employes = data.employes.length;
        this.stats.depenses = data.depenses.reduce((sum, d) => sum + d.montant, 0);
        this.stats.alertes = data.alertes.length;
        
        this.recentChantiers = data.chantiers.slice(0, 5);
        this.alertes = data.alertes;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }
}

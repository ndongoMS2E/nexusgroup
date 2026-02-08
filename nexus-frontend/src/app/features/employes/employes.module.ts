import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { EmployesComponent } from './components/employes.component';

const routes: Routes = [
  { path: '', component: EmployesComponent }
];

@NgModule({
  declarations: [EmployesComponent],
  imports: [
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class EmployesModule {}

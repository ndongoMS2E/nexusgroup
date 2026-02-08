import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { DepensesComponent } from './components/depenses.component';

const routes: Routes = [
  { path: '', component: DepensesComponent }
];

@NgModule({
  declarations: [DepensesComponent],
  imports: [
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class DepensesModule {}

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { PointageComponent } from './components/pointage.component';

const routes: Routes = [
  { path: '', component: PointageComponent }
];

@NgModule({
  declarations: [PointageComponent],
  imports: [
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class PointageModule {}

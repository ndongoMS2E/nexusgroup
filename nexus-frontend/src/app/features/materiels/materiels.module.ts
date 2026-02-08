import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { MaterielsComponent } from './components/materiels.component';

const routes: Routes = [
  { path: '', component: MaterielsComponent }
];

@NgModule({
  declarations: [MaterielsComponent],
  imports: [
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class MaterielsModule {}

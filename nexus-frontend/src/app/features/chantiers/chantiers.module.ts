import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { ChantiersComponent } from './components/chantiers.component';

const routes: Routes = [
  { path: '', component: ChantiersComponent }
];

@NgModule({
  declarations: [ChantiersComponent],
  imports: [
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class ChantiersModule {}

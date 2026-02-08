import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { DocumentsComponent } from './components/documents.component';

const routes: Routes = [
  { path: '', component: DocumentsComponent }
];

@NgModule({
  declarations: [DocumentsComponent],
  imports: [
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class DocumentsModule {}

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { SidebarComponent } from './components/sidebar/sidebar.component';
import { ModalComponent } from './components/modal/modal.component';
import { LayoutComponent } from './components/layout/layout.component';
import { MoneyPipe } from './pipes/money.pipe';

@NgModule({
  declarations: [
    SidebarComponent,
    ModalComponent,
    LayoutComponent,
    MoneyPipe
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule
  ],
  exports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    SidebarComponent,
    ModalComponent,
    LayoutComponent,
    MoneyPipe
  ]
})
export class SharedModule {}

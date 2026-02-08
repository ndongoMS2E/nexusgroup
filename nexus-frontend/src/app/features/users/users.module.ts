import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { UsersComponent } from './components/users.component';

const routes: Routes = [
  { path: '', component: UsersComponent }
];

@NgModule({
  declarations: [UsersComponent],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes)
  ]
})
export class UsersModule {}

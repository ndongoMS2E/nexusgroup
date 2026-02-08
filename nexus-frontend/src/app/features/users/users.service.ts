import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: string;
  chantier_id?: number;
  is_active: boolean;
  created_at?: string;
  last_login?: string;
}

export interface CreateUser {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: string;
  chantier_id?: number;
}

export interface Role {
  code: string;
  name: string;
  description: string;
  color: string;
  icon: string;
  level: number;
}

@Injectable({
  providedIn: 'root'
})
export class UsersService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.apiUrl}/auth/users`);
  }

  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(`${this.apiUrl}/auth/roles`);
  }

  createUser(data: CreateUser): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/auth/register`, data);
  }

  updateUserRole(userId: number, role: string, chantierId?: number): Observable<any> {
    let url = `${this.apiUrl}/auth/users/${userId}/role?role=${role}`;
    if (chantierId) {
      url += `&chantier_id=${chantierId}`;
    }
    return this.http.put(url, {});
  }

  activateUser(userId: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/auth/users/${userId}/activate`, {});
  }

  deactivateUser(userId: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/auth/users/${userId}/deactivate`, {});
  }
}

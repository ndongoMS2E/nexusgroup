import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Chantier, CreateChantier, UpdateChantier } from '../models';

@Injectable({
  providedIn: 'root'
})
export class ChantierService {
  private apiUrl = `${environment.apiUrl}/chantiers`;

  constructor(private http: HttpClient) {}

  getAll(): Observable<Chantier[]> {
    return this.http.get<Chantier[]>(`${this.apiUrl}/`);
  }

  getById(id: number): Observable<Chantier> {
    return this.http.get<Chantier>(`${this.apiUrl}/${id}`);
  }

  create(chantier: CreateChantier): Observable<Chantier> {
    return this.http.post<Chantier>(`${this.apiUrl}/`, chantier);
  }

  update(id: number, chantier: UpdateChantier): Observable<Chantier> {
    return this.http.put<Chantier>(`${this.apiUrl}/${id}`, chantier);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  downloadRapport(id: number): void {
    const token = localStorage.getItem('token');
    window.open(`${environment.apiUrl}/rapports/chantier/${id}/pdf?token=${token}`, '_blank');
  }
}

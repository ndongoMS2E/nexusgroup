import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Depense, CreateDepense } from '../models';

@Injectable({
  providedIn: 'root'
})
export class DepenseService {
  private apiUrl = `${environment.apiUrl}/depenses`;

  constructor(private http: HttpClient) {}

  getAll(): Observable<Depense[]> {
    return this.http.get<Depense[]>(`${this.apiUrl}/`);
  }

  getByChantier(chantierId: number): Observable<Depense[]> {
    return this.http.get<Depense[]>(`${this.apiUrl}/chantier/${chantierId}`);
  }

  create(depense: CreateDepense): Observable<Depense> {
    return this.http.post<Depense>(`${this.apiUrl}/`, depense);
  }

  approve(id: number): Observable<Depense> {
    return this.http.put<Depense>(`${this.apiUrl}/${id}/approve`, {});
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  getTotalDepenses(depenses: Depense[]): number {
    return depenses.reduce((sum, d) => sum + d.montant, 0);
  }
}

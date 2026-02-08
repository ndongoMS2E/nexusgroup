import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Materiel, CreateMateriel, CreateMouvement } from '../models';

@Injectable({
  providedIn: 'root'
})
export class MaterielService {
  private apiUrl = `${environment.apiUrl}/materiels`;

  constructor(private http: HttpClient) {}

  getAll(): Observable<Materiel[]> {
    return this.http.get<Materiel[]>(`${this.apiUrl}/`);
  }

  getByChantier(chantierId: number): Observable<Materiel[]> {
    return this.http.get<Materiel[]>(`${this.apiUrl}/chantier/${chantierId}`);
  }

  getAlertes(): Observable<Materiel[]> {
    return this.http.get<Materiel[]>(`${this.apiUrl}/alertes/`);
  }

  create(materiel: CreateMateriel): Observable<Materiel> {
    return this.http.post<Materiel>(`${this.apiUrl}/`, materiel);
  }

  update(id: number, materiel: Partial<CreateMateriel>): Observable<Materiel> {
    return this.http.put<Materiel>(`${this.apiUrl}/${id}`, materiel);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  createMouvement(mouvement: CreateMouvement): Observable<any> {
    return this.http.post(`${this.apiUrl}/mouvements/`, mouvement);
  }
}

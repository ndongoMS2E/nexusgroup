import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Employe, CreateEmploye, PointageEmploye, CreatePointage } from '../models';

@Injectable({
  providedIn: 'root'
})
export class EmployeService {
  private apiUrl = `${environment.apiUrl}/employes`;

  constructor(private http: HttpClient) {}

  getAll(chantierId?: number): Observable<Employe[]> {
    const url = chantierId ? `${this.apiUrl}/?chantier_id=${chantierId}` : `${this.apiUrl}/`;
    return this.http.get<Employe[]>(url);
  }

  getNonAffectes(): Observable<Employe[]> {
    return this.http.get<Employe[]>(`${this.apiUrl}/non-affectes`);
  }

  getById(id: number): Observable<Employe> {
    return this.http.get<Employe>(`${this.apiUrl}/${id}`);
  }

  create(employe: CreateEmploye): Observable<Employe> {
    return this.http.post<Employe>(`${this.apiUrl}/`, employe);
  }

  update(id: number, data: Partial<Employe>): Observable<Employe> {
    return this.http.put<Employe>(`${this.apiUrl}/${id}`, data);
  }

  affecter(id: number, chantierId: number | null): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}/affecter`, { chantier_id: chantierId });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  // Pointage
  getPointageJour(chantierId: number, date: string): Observable<PointageEmploye[]> {
    return this.http.get<PointageEmploye[]>(`${this.apiUrl}/pointage/${chantierId}/${date}`);
  }

  enregistrerPointage(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/pointage/`, data);
  }

  pointageMasse(chantierId: number, date: string, pointages: CreatePointage[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/pointage/masse/?chantier_id=${chantierId}&date_pointage=${date}`, pointages);
  }

  // Salaires
  calculerSalaires(chantierId: number, dateDebut: string, dateFin: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/salaires/${chantierId}?date_debut=${dateDebut}&date_fin=${dateFin}`);
  }
}

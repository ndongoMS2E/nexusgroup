import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Document } from '../models';

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private apiUrl = `${environment.apiUrl}/documents`;

  constructor(private http: HttpClient) {}

  getAll(): Observable<Document[]> {
    return this.http.get<Document[]>(`${this.apiUrl}/`);
  }

  getByChantier(chantierId: number): Observable<Document[]> {
    return this.http.get<Document[]>(`${this.apiUrl}/chantier/${chantierId}`);
  }

  upload(formData: FormData): Observable<Document> {
    return this.http.post<Document>(`${this.apiUrl}/upload/`, formData);
  }

  download(id: number): void {
    window.open(`${this.apiUrl}/download/${id}`, '_blank');
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  getIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'photo': '🖼️',
      'plan': '📐',
      'facture': '🧾',
      'contrat': '📝',
      'rapport': '📊'
    };
    return icons[type] || '📄';
  }
}

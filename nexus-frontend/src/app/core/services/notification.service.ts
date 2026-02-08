import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Notification } from '../models';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private apiUrl = `${environment.apiUrl}/notifications`;
  private countSubject = new BehaviorSubject<number>(0);
  public count$ = this.countSubject.asObservable();

  constructor(private http: HttpClient) {}

  getAll(): Observable<Notification[]> {
    return this.http.get<Notification[]>(`${this.apiUrl}/`);
  }

  getCount(): Observable<{ count: number }> {
    return this.http.get<{ count: number }>(`${this.apiUrl}/count`).pipe(
      tap(data => this.countSubject.next(data.count))
    );
  }

  markAsRead(id: number): Observable<Notification> {
    return this.http.put<Notification>(`${this.apiUrl}/${id}/read`, {});
  }

  markAllAsRead(): Observable<any> {
    return this.http.put(`${this.apiUrl}/read-all`, {});
  }

  getIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'info': 'ℹ️',
      'warning': '⚠️',
      'danger': '🚨',
      'success': '✅'
    };
    return icons[type] || '🔔';
  }

  refreshCount(): void {
    this.getCount().subscribe();
  }
}

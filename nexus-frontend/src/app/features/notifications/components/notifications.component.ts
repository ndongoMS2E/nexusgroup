import { Component, OnInit } from '@angular/core';
import { NotificationService } from '../../../core/services';
import { Notification } from '../../../core/models';

@Component({
  selector: 'app-notifications',
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.scss']
})
export class NotificationsComponent implements OnInit {
  notifications: Notification[] = [];
  isLoading = false;

  constructor(private notificationService: NotificationService) {}

  ngOnInit(): void {
    this.loadNotifications();
  }

  loadNotifications(): void {
    this.isLoading = true;
    this.notificationService.getAll().subscribe({
      next: (data) => {
        this.notifications = data;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  markAsRead(id: number): void {
    this.notificationService.markAsRead(id).subscribe({
      next: () => {
        this.loadNotifications();
        this.notificationService.refreshCount();
      }
    });
  }

  markAllAsRead(): void {
    this.notificationService.markAllAsRead().subscribe({
      next: () => {
        this.loadNotifications();
        this.notificationService.refreshCount();
      }
    });
  }

  getIcon(type: string): string {
    return this.notificationService.getIcon(type);
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR');
  }
}

import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { CoreModule } from './core/core.module';
import { SharedModule } from './shared/shared.module';

// Intercepteurs HTTP
import { httpInterceptorProviders } from './core/interceptors/http.interceptor';

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    CoreModule,
    SharedModule
  ],
  providers: [
    provideHttpClient(withInterceptorsFromDi()),  // ⬅️ Angular 17+ avec intercepteurs DI
    httpInterceptorProviders
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}

import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'money'
})
export class MoneyPipe implements PipeTransform {
  transform(value: number | null | undefined, currency: string = 'FCFA'): string {
    if (value === null || value === undefined) {
      return '0 ' + currency;
    }
    return new Intl.NumberFormat('fr-FR').format(value) + ' ' + currency;
  }
}

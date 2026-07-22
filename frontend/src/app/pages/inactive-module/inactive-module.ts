import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

@Component({
  selector: 'app-inactive-module-page',
  imports: [RouterLink],
  templateUrl: './inactive-module.html',
  styleUrl: './inactive-module.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InactiveModulePage {
  private readonly route = inject(ActivatedRoute);
  readonly titulo = this.route.snapshot.data['titulo'] as string;
}

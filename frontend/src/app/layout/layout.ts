import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './layout.html',
  styleUrl: './layout.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Layout implements OnInit {
  readonly auth = inject(AuthService);
  readonly menuAbierto = signal(false);
  readonly modoOscuro = signal(document.documentElement.dataset['theme'] === 'dark');

  ngOnInit(): void {
    if (!this.auth.usuario()) this.auth.cargarUsuario().subscribe();
  }

  cambiarTema(): void {
    const oscuro = !this.modoOscuro();
    this.modoOscuro.set(oscuro);
    document.documentElement.dataset['theme'] = oscuro ? 'dark' : 'light';
    localStorage.setItem('itdata-theme', oscuro ? 'dark' : 'light');
    window.dispatchEvent(new CustomEvent('itdata-theme-change'));
  }
}

import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { OpcionCatalogo, Rol, UsuarioGestion } from '../../core/models';

@Component({
  selector: 'app-settings-page',
  imports: [FormsModule, ReactiveFormsModule],
  templateUrl: './settings.html',
  styleUrl: './settings.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly usuarios = signal<UsuarioGestion[]>([]);
  readonly sucursales = signal<OpcionCatalogo[]>([]);
  readonly cargando = signal(true);
  readonly guardando = signal(false);
  readonly formularioVisible = signal(false);
  readonly editandoId = signal<string | null>(null);
  readonly error = signal('');
  search = '';

  readonly form = this.fb.group({
    username: ['', Validators.required],
    password: [''],
    first_name: ['', Validators.required],
    last_name: [''],
    email: ['', Validators.email],
    telefono: [''],
    rol: ['TECNICO' as Rol, Validators.required],
    sucursal: [''],
    sucursales_asignadas: [[] as string[]],
    activo_operativamente: [true],
    is_active: [true],
  });

  get rolesDisponibles(): Array<{ value: Rol; label: string }> {
    const roles: Array<{ value: Rol; label: string }> = [
      { value: 'TECNICO', label: 'Técnico' },
      { value: 'JDISTRITO', label: 'Jefe de Distrito' },
      { value: 'SUCURSAL', label: 'Sucursal' },
      { value: 'CONSULTOR', label: 'Consultor' },
    ];
    if (this.auth.usuario()?.rol === 'ADMINISTRADOR') {
      roles.unshift({ value: 'SUPERVISOR', label: 'Supervisor' });
      roles.unshift({ value: 'ADMINISTRADOR', label: 'Administrador' });
    }
    return roles;
  }

  ngOnInit(): void {
    if (this.auth.usuario()) {
      this.inicializar();
      return;
    }
    this.auth.cargarUsuario().subscribe({
      next: () => this.inicializar(),
      error: () => void this.router.navigate(['/login']),
    });
  }

  private inicializar(): void {
    if (!this.auth.puedeConfigurar()) {
      void this.router.navigate(['/dashboard']);
      return;
    }
    this.api.sucursales().subscribe((pagina) => this.sucursales.set(pagina.results));
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.api.usuarios(this.search).subscribe({
      next: (pagina) => this.usuarios.set(pagina.results),
      complete: () => this.cargando.set(false),
      error: () => this.cargando.set(false),
    });
  }

  nuevo(): void {
    this.editandoId.set(null);
    this.form.reset({
      username: '', password: '', first_name: '', last_name: '', email: '', telefono: '',
      rol: 'TECNICO', sucursal: '', sucursales_asignadas: [],
      activo_operativamente: true, is_active: true,
    });
    this.error.set('');
    this.formularioVisible.set(true);
  }

  editar(usuario: UsuarioGestion): void {
    this.editandoId.set(usuario.id);
    this.form.reset({
      username: usuario.username, password: '', first_name: usuario.first_name,
      last_name: usuario.last_name, email: usuario.email, telefono: usuario.telefono, rol: usuario.rol,
      sucursal: usuario.sucursal ?? '', sucursales_asignadas: usuario.sucursales_asignadas,
      activo_operativamente: usuario.activo_operativamente, is_active: usuario.is_active,
    });
    this.error.set('');
    this.formularioVisible.set(true);
  }

  guardar(): void {
    if (this.form.invalid || this.guardando()) return;
    const datos: Record<string, unknown> = { ...this.form.getRawValue() };
    if (!datos['password']) delete datos['password'];
    if (!datos['sucursal']) datos['sucursal'] = null;
    this.guardando.set(true);
    this.error.set('');
    const request = this.editandoId()
      ? this.api.actualizarUsuario(this.editandoId()!, datos)
      : this.api.crearUsuario(datos);
    request.subscribe({
      next: () => { this.formularioVisible.set(false); this.cargar(); },
      error: () => { this.error.set('No se pudo guardar. Verificá el rol, contraseña y asignaciones.'); this.guardando.set(false); },
      complete: () => this.guardando.set(false),
    });
  }

  desactivar(usuario: UsuarioGestion): void {
    if (!confirm(`¿Desactivar el acceso de ${usuario.nombre_completo}?`)) return;
    this.api.desactivarUsuario(usuario.id).subscribe(() => this.cargar());
  }

  textoRol(rol: string): string {
    return rol.replaceAll('_', ' ');
  }
}

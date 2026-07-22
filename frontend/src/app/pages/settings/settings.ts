import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ActivoGestion, CategoriaGestion, OpcionCatalogo, Rol, SubcategoriaGestion, UsuarioGestion } from '../../core/models';

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
  readonly activos = signal<ActivoGestion[]>([]);
  readonly sucursales = signal<OpcionCatalogo[]>([]);
  readonly tiposActivo = signal<OpcionCatalogo[]>([]);
  readonly criticidades = signal<OpcionCatalogo[]>([]);
  readonly categoriasGestion = signal<CategoriaGestion[]>([]);
  readonly subcategoriasGestion = signal<SubcategoriaGestion[]>([]);
  readonly seccion = signal<'usuarios' | 'activos' | 'categorias'>('usuarios');
  readonly cargando = signal(true);
  readonly guardando = signal(false);
  readonly formularioVisible = signal(false);
  readonly editandoId = signal<string | null>(null);
  readonly error = signal('');
  readonly formularioActivoVisible = signal(false);
  readonly editandoActivoId = signal<string | null>(null);
  readonly editandoCategoriaId = signal<string | null>(null);
  readonly editandoSubcategoriaId = signal<string | null>(null);
  search = '';
  searchActivo = '';

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

  readonly formActivo = this.fb.group({
    codigo: ['', Validators.required], nombre: ['', Validators.required],
    tipo_activo: ['', Validators.required], sucursal: [''],
    criticidad: ['', Validators.required], marca: [''], modelo: [''],
    numero_serie: [''], direccion_ip: [''], estado: ['OPERATIVO', Validators.required],
    activo: [true],
  });

  readonly formCategoria = this.fb.group({
    nombre: ['', Validators.required], descripcion: [''], activo: [true],
  });

  readonly formSubcategoria = this.fb.group({
    categoria: ['', Validators.required], nombre: ['', Validators.required],
    descripcion: [''], activo: [true],
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

  cambiarSeccion(seccion: 'usuarios' | 'activos' | 'categorias'): void {
    this.seccion.set(seccion);
    this.error.set('');
    if (seccion === 'activos') this.cargarActivos();
    else if (seccion === 'categorias') this.cargarCategoriasGestion();
    else this.cargar();
  }

  cargarCategoriasGestion(): void {
    this.cargando.set(true);
    forkJoin({ categorias: this.api.categoriasGestion(), subcategorias: this.api.subcategoriasGestion() }).subscribe({
      next: ({ categorias, subcategorias }) => { this.categoriasGestion.set(categorias); this.subcategoriasGestion.set(subcategorias); },
      complete: () => this.cargando.set(false), error: () => this.cargando.set(false),
    });
  }

  editarCategoria(item?: CategoriaGestion): void {
    this.editandoCategoriaId.set(item?.id ?? null);
    this.formCategoria.reset({ nombre: item?.nombre ?? '', descripcion: item?.descripcion ?? '', activo: item?.activo ?? true });
  }

  guardarCategoria(): void {
    if (this.formCategoria.invalid || this.guardando()) return;
    this.guardando.set(true); this.error.set('');
    const id = this.editandoCategoriaId();
    const peticion = id ? this.api.actualizarCategoria(id, this.formCategoria.getRawValue()) : this.api.crearCategoria(this.formCategoria.getRawValue());
    peticion.subscribe({ next: () => { this.editarCategoria(); this.cargarCategoriasGestion(); }, error: (e) => { this.error.set(e?.error?.nombre?.[0] ?? 'No se pudo guardar la categoría.'); this.guardando.set(false); }, complete: () => this.guardando.set(false) });
  }

  editarSubcategoria(item?: SubcategoriaGestion): void {
    this.editandoSubcategoriaId.set(item?.id ?? null);
    this.formSubcategoria.reset({ categoria: item?.categoria ?? '', nombre: item?.nombre ?? '', descripcion: item?.descripcion ?? '', activo: item?.activo ?? true });
  }

  guardarSubcategoria(): void {
    if (this.formSubcategoria.invalid || this.guardando()) return;
    this.guardando.set(true); this.error.set('');
    const id = this.editandoSubcategoriaId();
    const peticion = id ? this.api.actualizarSubcategoria(id, this.formSubcategoria.getRawValue()) : this.api.crearSubcategoria(this.formSubcategoria.getRawValue());
    peticion.subscribe({ next: () => { this.editarSubcategoria(); this.cargarCategoriasGestion(); }, error: (e) => { this.error.set(e?.error?.non_field_errors?.[0] ?? 'No se pudo guardar la subcategoría.'); this.guardando.set(false); }, complete: () => this.guardando.set(false) });
  }

  desactivarCategoria(item: CategoriaGestion): void { if (confirm(`¿Desactivar la categoría ${item.nombre}?`)) this.api.desactivarCategoria(item.id).subscribe(() => this.cargarCategoriasGestion()); }
  desactivarSubcategoria(item: SubcategoriaGestion): void { if (confirm(`¿Desactivar la subcategoría ${item.nombre}?`)) this.api.desactivarSubcategoria(item.id).subscribe(() => this.cargarCategoriasGestion()); }
  nombreCategoria(id: string): string { return this.categoriasGestion().find((item) => item.id === id)?.nombre ?? '—'; }

  cargarActivos(): void {
    this.cargando.set(true);
    this.api.activos(this.searchActivo).subscribe({
      next: (pagina) => this.activos.set(pagina.results),
      complete: () => this.cargando.set(false), error: () => this.cargando.set(false),
    });
  }

  nuevoActivo(): void {
    this.editandoActivoId.set(null);
    this.formActivo.reset({ codigo: '', nombre: '', tipo_activo: '', sucursal: '', criticidad: '', marca: '', modelo: '', numero_serie: '', direccion_ip: '', estado: 'OPERATIVO', activo: true });
    this.cargarCatalogosActivo(); this.error.set(''); this.formularioActivoVisible.set(true);
  }

  editarActivo(activo: ActivoGestion): void {
    this.editandoActivoId.set(activo.id);
    this.formActivo.reset({ codigo: activo.codigo, nombre: activo.nombre, tipo_activo: activo.tipo_activo, sucursal: activo.sucursal ?? '', criticidad: activo.criticidad, marca: activo.marca, modelo: activo.modelo, numero_serie: activo.numero_serie, direccion_ip: activo.direccion_ip ?? '', estado: activo.estado, activo: activo.activo });
    this.cargarCatalogosActivo(); this.error.set(''); this.formularioActivoVisible.set(true);
  }

  private cargarCatalogosActivo(): void {
    if (this.tiposActivo().length && this.criticidades().length) return;
    forkJoin({ tipos: this.api.tiposActivo(), criticidades: this.api.criticidades() }).subscribe(({ tipos, criticidades }) => { this.tiposActivo.set(tipos); this.criticidades.set(criticidades); });
  }

  guardarActivo(): void {
    if (this.formActivo.invalid || this.guardando()) return;
    const datos: Record<string, unknown> = { ...this.formActivo.getRawValue() };
    if (!datos['sucursal']) datos['sucursal'] = null;
    if (!datos['direccion_ip']) datos['direccion_ip'] = null;
    this.guardando.set(true); this.error.set('');
    const request = this.editandoActivoId() ? this.api.actualizarActivo(this.editandoActivoId()!, datos) : this.api.crearActivo(datos);
    request.subscribe({ next: () => { this.formularioActivoVisible.set(false); this.cargarActivos(); }, error: (e) => { this.error.set(e?.error?.codigo?.[0] ?? 'No se pudo guardar el activo. Revisá los datos y catálogos.'); this.guardando.set(false); }, complete: () => this.guardando.set(false) });
  }

  desactivarActivo(activo: ActivoGestion): void {
    if (!confirm(`¿Desactivar el activo ${activo.codigo}?`)) return;
    this.api.desactivarActivo(activo.id).subscribe(() => this.cargarActivos());
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

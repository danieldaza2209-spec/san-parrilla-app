import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const isVercel = Boolean(process.env.VERCEL || process.env.AWS_REGION || process.env.LAMBDA_TASK_ROOT);

// Categorías del Menú Almuerzos
export const lunchCategories = [
  { id: 'especiales_hoy', name: 'Especiales de Hoy', sort_order: 1 },
  { id: 'fuertes_165', name: 'Platos Fuertes $16.500', sort_order: 2 },
  { id: 'fuertes_175', name: 'Platos Fuertes $17.500', sort_order: 3 },
  { id: 'especiales_21', name: 'Especiales & Parrilladas', sort_order: 4 },
  { id: 'picadas', name: 'Picadas Especiales', sort_order: 5 },
  { id: 'bebidas', name: 'Bebidas y Adicionales', sort_order: 6 },
];

// Categorías del Menú Comidas Rápidas (Turno Noche)
export const rapidasCategories = [
  { id: 'hamburguesas', name: 'Hamburguesas', icon: '🍔', sort_order: 20 },
  { id: 'perros_calientes', name: 'Perros Calientes', icon: '🌭', sort_order: 21 },
  { id: 'salchipapas_papas_locas', name: 'Salchipapas y Papas Locas', icon: '🍟', sort_order: 22 },
  { id: 'patacones', name: 'Patacones', icon: '🫓', sort_order: 23 },
  { id: 'sandwich', name: 'Sándwich', icon: '🥪', sort_order: 24 },
  { id: 'picadas_noche', name: 'Picadas Noche', icon: '🥩', sort_order: 25 },
  { id: 'especiales_noche', name: 'Especiales Noche', icon: '🔥', sort_order: 26 },
  { id: 'granizados_jugos', name: 'Granizados y Jugos', icon: '🥤', sort_order: 27 },
  { id: 'bebidas_rapidas', name: 'Bebidas', icon: '🧊', sort_order: 28 },
];

export const fallbackCategories = [...lunchCategories, ...rapidasCategories];

export const fallbackDailySpecials = {
  sopa: 'Campesina',
  principios: ['Calabacín al huevo', 'Lentejas caseras', 'Frijoles caseros'],
  acompanamientos: ['Puré de ahuyama', 'Deditos', 'Tajadas maduras'],
  updated_at: new Date().toISOString()
};

export const lunchProductList = [
  // Plato de Prueba de Impresión Térmica SAT Q22
  { id: 'test-print-sat', name: '🔥 Combo Prueba Impresión SAT Q22', price: 1000, category_id: 'fuertes_165', description: 'Plato de prueba rápida para calibrar corte e impresión en impresora térmica SAT Q22 (80mm).', is_active: 1, is_featured: 1, sort_order: -999, menu_type: 'almuerzo' },

  // $16.500
  { id: 't1-0', name: 'Milanesa de pollo', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 't1-1', name: 'Nuggets de pollo', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 't1-2', name: 'Pernil frito', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 't1-3', name: 'Pernil bbq', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 3 },
  { id: 't1-4', name: 'Lomo de cerdo a la plancha', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 4 },
  { id: 't1-5', name: 'Hígado en bistec', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 5 },
  { id: 't1-6', name: 'Chuleta de cerdo', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 6 },
  { id: 't1-7', name: 'Hígado al ajillo', price: 16500, category_id: 'fuertes_165', description: 'Especial del día. Incluye sopa, principio y acompañamiento.', is_active: 1, is_featured: 1, sort_order: 7, special_badge: '⭐ SOLO POR HOY' },
  { id: 't1-8', name: 'Desgranado de carne', price: 16500, category_id: 'fuertes_165', description: 'Especial del día. Incluye sopa, principio y acompañamiento.', is_active: 1, is_featured: 1, sort_order: 8, special_badge: '⭐ SOLO POR HOY' },

  // $17.500
  { id: 't2-0', name: 'Carne a la plancha', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 't2-1', name: 'Carne en bistec', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 't2-2', name: 'Carne bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 't2-3', name: 'Pechuga a la plancha', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 3 },
  { id: 't2-4', name: 'Pechuga en salsa criolla', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 4 },
  { id: 't2-5', name: 'Pechuga apanada', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 5 },
  { id: 't2-6', name: 'Pechuga bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 6 },
  { id: 't2-6b', name: 'Pechuga al ajillo', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 6 },
  { id: 't2-7', name: 'Pernil hawaiano', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 7 },
  { id: 't2-8', name: 'Lomo de cerdo a la bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 8 },
  { id: 't2-9', name: 'Lomo de cerdo al ajillo', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 9 },
  { id: 't2-10', name: 'Chuleta de cerdo al ajillo', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 10 },
  { id: 't2-11', name: 'Chuleta de cerdo a la bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 11 },

  // $18.000
  { id: 't3-0', name: 'Bandeja paisa', price: 18000, category_id: 'fuertes_175', description: 'Plato típico tradicional con carne, chicharrón, huevo, arroz y frijol.', is_active: 1, is_featured: 1, sort_order: 12 },
  { id: 't3-1', name: 'Alitas bbq', price: 18000, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 13 },
  { id: 't3-2', name: 'Creps de pollo', price: 18000, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 14 },
  { id: 't3-3', name: 'Bistec a caballo', price: 18000, category_id: 'fuertes_175', description: 'Carne en salsa criolla coronada con huevo frito.', is_active: 1, is_featured: 0, sort_order: 15 },
  { id: 't3-4', name: 'Pechuga hawaiana', price: 18000, category_id: 'fuertes_175', description: 'Pechuga gratinada con piña caramelizada y queso.', is_active: 1, is_featured: 0, sort_order: 16 },
  { id: 't3-4b', name: 'Pechuga en salsa bechamel', price: 18000, category_id: 'fuertes_175', description: 'Pechuga bañada en salsa bechamel casera. Incluye sopa, principio y acompañamiento.', is_active: 1, is_featured: 0, sort_order: 16 },
  { id: 't3-5', name: 'Combo Personal', price: 18000, category_id: 'fuertes_175', description: 'Opción rápida del asador.', is_active: 1, is_featured: 0, sort_order: 17 },
  { id: 't3-6', name: 'Arroz ranchero', price: 18000, category_id: 'fuertes_175', description: 'Arroz especial de la casa con carnes y maíz.', is_active: 1, is_featured: 1, sort_order: 18, special_badge: '⭐ SOLO LOS LUNES' },

  // $21.000
  { id: 'esp-0', name: 'Sobrebarriga dorada', price: 21000, category_id: 'especiales_21', description: 'Corte suave y dorado a las brasas.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 'esp-1', name: 'Bagre frito', price: 21000, category_id: 'especiales_21', description: 'Pescado fresco del día con patacón.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 'esp-2', name: 'Bagre al ajillo', price: 21000, category_id: 'especiales_21', description: 'Bañado en reducción cremosa de ajo y finas hierbas.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 'esp-3', name: 'Róbalo apanado', price: 21000, category_id: 'especiales_21', description: 'Filete de róbalo crocante.', is_active: 1, is_featured: 0, sort_order: 3 },
  { id: 'esp-4', name: 'Róbalo al ajillo', price: 21000, category_id: 'especiales_21', description: 'Filete bañado en salsa de ajillo.', is_active: 1, is_featured: 0, sort_order: 4 },

  // $22.000
  { id: 'esp-5', name: 'Bagre sudado', price: 22000, category_id: 'especiales_21', description: 'En jugo natural de tomate criollo y cebolla.', is_active: 1, is_featured: 0, sort_order: 5 },
  { id: 'esp-6', name: 'Bagre frito sudado', price: 22000, category_id: 'especiales_21', description: 'Bagre frito bañado en salsa criolla sudada.', is_active: 1, is_featured: 0, sort_order: 6 },
  { id: 'esp-7', name: 'Mojarra frita', price: 22000, category_id: 'especiales_21', description: 'Mojarra entera frita bien crocante con patacones.', is_active: 1, is_featured: 0, sort_order: 7 },
  { id: 'esp-8', name: 'Mojarra sudada', price: 22000, category_id: 'especiales_21', description: 'Mojarra entera en salsa criolla casera.', is_active: 1, is_featured: 0, sort_order: 8 },
  { id: 'esp-9', name: 'Mojarra frita sudada', price: 22000, category_id: 'especiales_21', description: 'Mojarra frita bañada en hogao y salsa criolla.', is_active: 1, is_featured: 0, sort_order: 9 },
  { id: 'esp-10', name: 'Mini cazuela de mariscos', price: 22000, category_id: 'especiales_21', description: 'Porción personal de cazuela cremosa de mariscos.', is_active: 1, is_featured: 0, sort_order: 10 },

  // $23.000
  { id: 'esp-11', name: 'Costillas bbq', price: 23000, category_id: 'especiales_21', description: 'Costillas ahumadas bañadas en salsa BBQ casera.', is_active: 1, is_featured: 0, sort_order: 11 },
  { id: 'esp-12', name: 'Pechuga con maíz gratinada', price: 23000, category_id: 'especiales_21', description: 'Pechuga a la plancha con crema de maíz y queso gratinado.', is_active: 1, is_featured: 0, sort_order: 12 },
  { id: 'esp-13', name: 'Pechuga en champiñones', price: 23000, category_id: 'especiales_21', description: 'Filete de pechuga con salsa cremosa de champiñones.', is_active: 1, is_featured: 0, sort_order: 13 },

  // $27.500
  { id: 'esp-14', name: 'Churrasco', price: 27500, category_id: 'especiales_21', description: 'Corte de res jugoso asado al carbón.', is_active: 1, is_featured: 1, sort_order: 14 },
  { id: 'esp-15', name: 'Parrillada', price: 27500, category_id: 'especiales_21', description: 'Combinación de carnes a la parrilla con papa salada y arepa.', is_active: 1, is_featured: 1, sort_order: 15 },
  { id: 'esp-16', name: 'Pechuga con tocineta y champ.', price: 27500, category_id: 'especiales_21', description: 'Pechuga gratinada con tocineta y champiñones.', is_active: 1, is_featured: 0, sort_order: 16 },
  { id: 'esp-17', name: 'Pollo Santo domingo', price: 27500, category_id: 'especiales_21', description: 'Receta tradicional San Parrilla.', is_active: 1, is_featured: 0, sort_order: 17 },
  { id: 'esp-18', name: 'Llanera mixta', price: 27500, category_id: 'especiales_21', description: 'Carne a la llanera con chunchullo y plátano.', is_active: 1, is_featured: 0, sort_order: 18 },
  { id: 'esp-19', name: 'Parrilla mixta', price: 27500, category_id: 'especiales_21', description: 'Res, cerdo y pollo a las brasas.', is_active: 1, is_featured: 1, sort_order: 19 },
  { id: 'esp-20', name: 'Carne grande', price: 27500, category_id: 'especiales_21', description: 'Porción generosa de carne asada para buen apetito.', is_active: 1, is_featured: 0, sort_order: 20 },
  { id: 'esp-21', name: 'Pechuga grande', price: 27500, category_id: 'especiales_21', description: 'Doble pechuga a la plancha.', is_active: 1, is_featured: 0, sort_order: 21 },
  { id: 'esp-22', name: 'Mini cazuela de camarones', price: 27500, category_id: 'especiales_21', description: 'Cazuela cremosa de camarones al ajillo.', is_active: 1, is_featured: 0, sort_order: 22 },
  { id: 'esp-23', name: 'Mini cazuela de bagre', price: 27500, category_id: 'especiales_21', description: 'Cazuela tradicional de bagre en leche de coco.', is_active: 1, is_featured: 0, sort_order: 23 },

  // $33.000
  { id: 'esp-24', name: 'Cazuela de mariscos', price: 33000, category_id: 'especiales_21', description: 'Cremosa y cargada de mariscos frescos.', is_active: 1, is_featured: 1, sort_order: 24 },
  { id: 'esp-25', name: 'Róbalo a la marinera', price: 33000, category_id: 'especiales_21', description: 'Filete coronado con mariscos en salsa.', is_active: 1, is_featured: 0, sort_order: 25 },
  { id: 'esp-26', name: 'Bagre a la marinera', price: 33000, category_id: 'especiales_21', description: 'Bagre bañado en salsa marinera.', is_active: 1, is_featured: 0, sort_order: 26 },
  { id: 'esp-27', name: 'Róbalo con camarones', price: 33000, category_id: 'especiales_21', description: 'Exquisito filete con camarones salteados.', is_active: 1, is_featured: 0, sort_order: 27 },

  // Picadas
  { id: 'pic-1', name: 'Picada x 1', price: 19500, category_id: 'picadas', description: 'Variedad de carnes y acompañamiento para una persona.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 'pic-2', name: 'Picada x 2', price: 30000, category_id: 'picadas', description: 'Perfecta para compartir en pareja. Incluye carnes, chorizo y papas.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 'pic-3', name: 'Picada x 3', price: 44000, category_id: 'picadas', description: 'Gran porción familiar para tres personas.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 'pic-4', name: 'Picada Berraca', price: 55000, category_id: 'picadas', description: 'Chicharrón crujiente, costilla, lomo y papitas criollas.', is_active: 1, is_featured: 1, sort_order: 3 },

  // Bebidas
  { id: 'beb-1', name: 'Gaseosa 400ml', price: 4000, category_id: 'bebidas', description: 'Postobón, Coca-Cola o Pepsi bien fría.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 'beb-2', name: 'Gaseosa 1.5L', price: 8000, category_id: 'bebidas', description: 'Ideal para compartir.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 'beb-3', name: 'Jugo Natural en Agua', price: 6000, category_id: 'bebidas', description: 'Mango, Maracuyá, Mora, Lulo o Fresa.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 'beb-4', name: 'Jugo Natural en Leche', price: 7500, category_id: 'bebidas', description: 'Cremoso y refrescante.', is_active: 1, is_featured: 0, sort_order: 3 },
  { id: 'beb-5', name: 'Cerveza Club Colombia / Águila', price: 5500, category_id: 'bebidas', description: 'Botella fría.', is_active: 1, is_featured: 0, sort_order: 4 },
  { id: 'beb-6', name: 'Porción de Papas a la Francesa', price: 6000, category_id: 'bebidas', description: 'Papas crocantes.', is_active: 1, is_featured: 0, sort_order: 5 },
  { id: 'beb-7', name: 'Porción de Patacón con Hogao', price: 6500, category_id: 'bebidas', description: 'Con hogao tradicional de la casa.', is_active: 1, is_featured: 0, sort_order: 6 },
];

export const rapidasProductList = [
  // Hamburguesas
  { id: 'rap-ham-1', name: 'Hamburguesa Clásica', price: 15500, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 1 },
  { id: 'rap-ham-2', name: 'Hamburguesa Chicken', price: 18000, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 2 },
  { id: 'rap-ham-3', name: 'Choriburguer', price: 20000, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 3 },
  { id: 'rap-ham-4', name: 'Hamburguesa Space', price: 20500, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 4 },
  { id: 'rap-ham-5', name: 'Hamburguesa Tentación', price: 22500, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 5 },
  { id: 'rap-ham-6', name: 'Big Burguer', price: 23500, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 6 },
  { id: 'rap-ham-7', name: 'Hamburguesa Crunch Master', price: 26000, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 7 },
  { id: 'rap-ham-8', name: 'Hamburguesa Berraca', price: 26000, category_id: 'hamburguesas', menu_type: 'rapidas', is_active: 1, sort_order: 8 },

  // Perros Calientes
  { id: 'rap-per-1', name: 'Perro Americano', price: 15500, category_id: 'perros_calientes', menu_type: 'rapidas', is_active: 1, sort_order: 9 },
  { id: 'rap-per-2', name: 'Choriperro', price: 16000, category_id: 'perros_calientes', menu_type: 'rapidas', is_active: 1, sort_order: 10 },
  { id: 'rap-per-3', name: 'Perro Hawaiano (Carne)', price: 17500, category_id: 'perros_calientes', menu_type: 'rapidas', is_active: 1, sort_order: 11 },
  { id: 'rap-per-4', name: 'Perro Hawaiano (Pollo)', price: 17500, category_id: 'perros_calientes', menu_type: 'rapidas', is_active: 1, sort_order: 12 },
  { id: 'rap-per-5', name: 'Perro Loco', price: 18500, category_id: 'perros_calientes', menu_type: 'rapidas', is_active: 1, sort_order: 13 },
  { id: 'rap-per-6', name: 'Perro Especial', price: 19500, category_id: 'perros_calientes', menu_type: 'rapidas', is_active: 1, sort_order: 14 },
  { id: 'rap-per-7', name: 'Perro Extra-Largo', price: 30000, category_id: 'perros_calientes', menu_type: 'rapidas', is_active: 1, sort_order: 15 },

  // Salchipapas y Papas Locas
  { id: 'rap-sal-1', name: 'Salchipapa Clásica', price: 15500, category_id: 'salchipapas_papas_locas', menu_type: 'rapidas', is_active: 1, sort_order: 16 },
  { id: 'rap-sal-2', name: 'Salchipapa Especial de Carne', price: 22000, category_id: 'salchipapas_papas_locas', menu_type: 'rapidas', is_active: 1, sort_order: 17 },
  { id: 'rap-sal-3', name: 'Salchipapa Especial de Pollo', price: 22000, category_id: 'salchipapas_papas_locas', menu_type: 'rapidas', is_active: 1, sort_order: 18 },
  { id: 'rap-pap-1', name: 'Papas Locas Clásicas (Carne)', price: 17000, category_id: 'salchipapas_papas_locas', menu_type: 'rapidas', is_active: 1, sort_order: 19 },
  { id: 'rap-pap-2', name: 'Papas Locas Clásicas (Pollo)', price: 17000, category_id: 'salchipapas_papas_locas', menu_type: 'rapidas', is_active: 1, sort_order: 20 },
  { id: 'rap-pap-3', name: 'Papas Locas Mixtas', price: 22000, category_id: 'salchipapas_papas_locas', menu_type: 'rapidas', is_active: 1, sort_order: 21 },
  { id: 'rap-pap-4', name: 'Papas Locas San Parrilla', price: 24000, category_id: 'salchipapas_papas_locas', menu_type: 'rapidas', is_active: 1, sort_order: 22 },

  // Patacones
  { id: 'rap-pat-1', name: 'Patacón Clásico (Carne)', price: 15500, category_id: 'patacones', menu_type: 'rapidas', is_active: 1, sort_order: 23 },
  { id: 'rap-pat-2', name: 'Patacón Clásico (Pollo)', price: 15500, category_id: 'patacones', menu_type: 'rapidas', is_active: 1, sort_order: 24 },
  { id: 'rap-pat-3', name: 'Patacón Porky', price: 17000, category_id: 'patacones', menu_type: 'rapidas', is_active: 1, sort_order: 25 },
  { id: 'rap-pat-4', name: 'Patacón Mixto', price: 19500, category_id: 'patacones', menu_type: 'rapidas', is_active: 1, sort_order: 26 },
  { id: 'rap-pat-5', name: 'Patacón San Parrilla', price: 21000, category_id: 'patacones', menu_type: 'rapidas', is_active: 1, sort_order: 27 },

  // Sándwich
  { id: 'rap-san-1', name: 'Sándwich Clásico (Carne)', price: 15500, category_id: 'sandwich', menu_type: 'rapidas', is_active: 1, sort_order: 28 },
  { id: 'rap-san-2', name: 'Sándwich Clásico (Pollo)', price: 15500, category_id: 'sandwich', menu_type: 'rapidas', is_active: 1, sort_order: 29 },
  { id: 'rap-san-3', name: 'Sándwich Granjero', price: 16500, category_id: 'sandwich', menu_type: 'rapidas', is_active: 1, sort_order: 30 },
  { id: 'rap-san-4', name: 'Sándwich Porky', price: 19500, category_id: 'sandwich', menu_type: 'rapidas', is_active: 1, sort_order: 31 },
  { id: 'rap-san-5', name: 'Sándwich San Parrilla', price: 21000, category_id: 'sandwich', menu_type: 'rapidas', is_active: 1, sort_order: 32 },

  // Picadas Noche
  { id: 'rap-pic-1', name: 'Picada Personal', price: 27500, category_id: 'picadas_noche', menu_type: 'rapidas', is_active: 1, sort_order: 33 },
  { id: 'rap-pic-2', name: 'Picada Dúo', price: 50000, category_id: 'picadas_noche', menu_type: 'rapidas', is_active: 1, sort_order: 34 },
  { id: 'rap-pic-3', name: 'Picada Trío', price: 66000, category_id: 'picadas_noche', menu_type: 'rapidas', is_active: 1, sort_order: 35 },
  { id: 'rap-pic-4', name: 'Picada Berraca Noche', price: 55000, category_id: 'picadas_noche', menu_type: 'rapidas', is_active: 1, sort_order: 36 },

  // Especiales Noche
  { id: 'rap-esp-1', name: 'Bandeja San Parrilla (Carne a la plancha)', price: 21000, category_id: 'especiales_noche', menu_type: 'rapidas', is_active: 1, sort_order: 37 },
  { id: 'rap-esp-2', name: 'Bandeja San Parrilla (Pechuga a la plancha)', price: 21000, category_id: 'especiales_noche', menu_type: 'rapidas', is_active: 1, sort_order: 38 },
  { id: 'rap-esp-3', name: 'Bandeja San Parrilla (Lomo a la plancha)', price: 21000, category_id: 'especiales_noche', menu_type: 'rapidas', is_active: 1, sort_order: 39 },
  { id: 'rap-esp-4', name: 'Bandeja San Parrilla (Chuleta a la plancha)', price: 21000, category_id: 'especiales_noche', menu_type: 'rapidas', is_active: 1, sort_order: 40 },
  { id: 'rap-esp-5', name: 'Alitas BBQ (Noche)', price: 22000, category_id: 'especiales_noche', menu_type: 'rapidas', is_active: 1, sort_order: 41 },
  { id: 'rap-esp-6', name: 'Alitas Apanadas', price: 22000, category_id: 'especiales_noche', menu_type: 'rapidas', is_active: 1, sort_order: 42 },
  { id: 'rap-esp-7', name: 'Costillitas BBQ', price: 23000, category_id: 'especiales_noche', menu_type: 'rapidas', is_active: 1, sort_order: 43 },

  // Granizados y Jugos
  { id: 'rap-jug-1', name: 'Jugo / Granizado en Agua', price: 8000, category_id: 'granizados_jugos', menu_type: 'rapidas', is_active: 1, sort_order: 44, has_flavor: 1 },
  { id: 'rap-jug-2', name: 'Jugo / Granizado en Leche', price: 9500, category_id: 'granizados_jugos', menu_type: 'rapidas', is_active: 1, sort_order: 45, has_flavor: 1 },
  { id: 'rap-jug-3', name: 'Limonada Cerezada', price: 10000, category_id: 'granizados_jugos', menu_type: 'rapidas', is_active: 1, sort_order: 46 },

  // Bebidas
  { id: 'rap-beb-1', name: 'Agua', price: 3000, category_id: 'bebidas_rapidas', menu_type: 'rapidas', is_active: 1, sort_order: 47 },
  { id: 'rap-beb-2', name: 'Soda', price: 4000, category_id: 'bebidas_rapidas', menu_type: 'rapidas', is_active: 1, sort_order: 48 },
  { id: 'rap-beb-3', name: 'Gaseosa P400', price: 4000, category_id: 'bebidas_rapidas', menu_type: 'rapidas', is_active: 1, sort_order: 49 },
  { id: 'rap-beb-4', name: 'Gaseosa 1.5L', price: 8000, category_id: 'bebidas_rapidas', menu_type: 'rapidas', is_active: 1, sort_order: 50 },
  { id: 'rap-beb-5', name: 'Gaseosa Mega', price: 13500, category_id: 'bebidas_rapidas', menu_type: 'rapidas', is_active: 1, sort_order: 51 },
  { id: 'rap-beb-6', name: 'Cerveza', price: 4500, category_id: 'bebidas_rapidas', menu_type: 'rapidas', is_active: 1, sort_order: 52 },
];

export const initialProductList = [...lunchProductList, ...rapidasProductList];

let db = null;

// Initialize SQLite only in non-serverless local environments
if (!isVercel) {
  try {
    const modName = 'node' + ':sqlite';
    const sqlite = require(modName);
    if (sqlite && sqlite.DatabaseSync) {
      const dataDir = path.resolve(__dirname, '../../data');
      if (!fs.existsSync(dataDir)) {
        try { fs.mkdirSync(dataDir, { recursive: true }); } catch (e) {}
      }
      const dbPath = path.join(dataDir, 'sanparrilla.db');
      db = new sqlite.DatabaseSync(dbPath);
      try { db.exec('PRAGMA foreign_keys = ON;'); } catch (e) {}
      db.exec(`
        CREATE TABLE IF NOT EXISTS categories (id TEXT PRIMARY KEY, name TEXT NOT NULL, sort_order INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT NOT NULL, price INTEGER NOT NULL, category_id TEXT NOT NULL, description TEXT DEFAULT '', is_active INTEGER DEFAULT 1, is_featured INTEGER DEFAULT 0, sort_order INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS daily_specials (id INTEGER PRIMARY KEY CHECK (id = 1), sopa TEXT NOT NULL, principios TEXT NOT NULL, acompanamientos TEXT NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL UNIQUE, address TEXT NOT NULL, neighborhood TEXT DEFAULT '', notes TEXT DEFAULT '', order_count INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS cash_registers (id INTEGER PRIMARY KEY AUTOINCREMENT, opened_at DATETIME DEFAULT CURRENT_TIMESTAMP, closed_at DATETIME, initial_cash INTEGER NOT NULL DEFAULT 0, status TEXT DEFAULT 'open', total_cash_sales INTEGER DEFAULT 0, total_nequi_sales INTEGER DEFAULT 0, total_daviplata_sales INTEGER DEFAULT 0, total_card_sales INTEGER DEFAULT 0, final_cash_counted INTEGER DEFAULT 0, cash_difference INTEGER DEFAULT 0, notes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_type TEXT NOT NULL, table_number TEXT, customer_id INTEGER, customer_name TEXT, customer_phone TEXT, delivery_address TEXT, delivery_neighborhood TEXT, delivery_notes TEXT, subtotal INTEGER NOT NULL, delivery_fee INTEGER DEFAULT 0, packaging_fee INTEGER DEFAULT 0, total INTEGER NOT NULL, payment_method TEXT NOT NULL, payment_change_for INTEGER DEFAULT 0, status TEXT DEFAULT 'completado', cash_register_id INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, product_name TEXT NOT NULL, price INTEGER NOT NULL, quantity INTEGER NOT NULL DEFAULT 1, notes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS views_counter (date TEXT PRIMARY KEY, views_count INTEGER DEFAULT 0);
      `);
      try {
        const insertCat = db.prepare('INSERT OR REPLACE INTO categories (id, name, sort_order) VALUES (?, ?, ?)');
        for (const c of fallbackCategories) {
          insertCat.run(c.id, c.name, c.sort_order);
        }
        // Sync products catalog with initialProductList
        db.exec('DELETE FROM products');
        const insertProd = db.prepare(`
          INSERT INTO products (id, name, price, category_id, description, is_active, is_featured, sort_order)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `);
        for (const p of initialProductList) {
          insertProd.run(p.id, p.name, p.price, p.category_id, p.description || '', p.is_active, p.is_featured, p.sort_order);
        }

        // Sync default daily specials if empty or outdated
        db.prepare(`
          INSERT OR REPLACE INTO daily_specials (id, sopa, principios, acompanamientos, updated_at)
          VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
        `).run(
          fallbackDailySpecials.sopa,
          JSON.stringify(fallbackDailySpecials.principios),
          JSON.stringify(fallbackDailySpecials.acompanamientos)
        );
        const cashCount = db.prepare('SELECT count(*) as count FROM cash_registers').get().count;
        if (cashCount === 0) {
          db.prepare("INSERT INTO cash_registers (initial_cash, status, notes) VALUES (100000, 'open', 'Apertura inicial')").run();
        }
      } catch (e) {}
    }
  } catch (err) {
    db = null;
  }
}

// In-memory runtime state (used if DB is unavailable, in Vercel or as high-speed cache)
let memProducts = [...initialProductList];
let memSpecials = { ...fallbackDailySpecials };
let memCustomers = [];
let memOrders = [];
let memCash = {
  id: 1,
  opened_at: new Date().toISOString(),
  closed_at: null,
  initial_cash: 100000,
  status: 'open',
  total_cash_sales: 0,
  total_nequi_sales: 0,
  total_daviplata_sales: 0,
  total_card_sales: 0,
  final_cash_counted: 0,
  cash_difference: 0,
  notes: 'Apertura inicial de caja'
};
let memViews = 1;

// ==========================================
// EXPORTED FUNCTIONS
// ==========================================

export function getCategories() {
  if (db) {
    try {
      const rows = db.prepare('SELECT * FROM categories ORDER BY sort_order ASC').all();
      if (rows && rows.length > 0) return rows;
    } catch (e) {}
  }
  return fallbackCategories;
}

export function getProducts(onlyActive = true) {
  if (db) {
    try {
      const rows = onlyActive
        ? db.prepare('SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order ASC').all()
        : db.prepare('SELECT * FROM products ORDER BY category_id, sort_order ASC').all();
      if (rows && rows.length > 0) return rows;
    } catch (e) {}
  }
  if (onlyActive) {
    return memProducts.filter(p => p.is_active === 1);
  }
  return memProducts;
}

// Productos de uso interno (solo visibles para el personal en el POS, nunca en la carta pública).
export const INTERNAL_PRODUCT_IDS = new Set(['test-print-sat']);

const badgeById = new Map(
  initialProductList.filter((p) => p.special_badge).map((p) => [p.id, p.special_badge])
);

export function getPublicProducts() {
  const rows = getProducts(true) || [];
  const source = rows.length > 0 ? rows : initialProductList;
  return source
    .filter((p) => !INTERNAL_PRODUCT_IDS.has(p.id))
    .map((p) => (badgeById.has(p.id) && !p.special_badge ? { ...p, special_badge: badgeById.get(p.id) } : p));
}

export function getDailySpecials() {
  if (db) {
    try {
      const row = db.prepare('SELECT * FROM daily_specials WHERE id = 1').get();
      if (row) {
        return {
          sopa: row.sopa,
          principios: JSON.parse(row.principios || '[]'),
          acompanamientos: JSON.parse(row.acompanamientos || '[]'),
          updated_at: row.updated_at
        };
      }
    } catch (e) {}
  }
  return memSpecials;
}

export function updateDailySpecials(sopa, principios, acompanamientos) {
  memSpecials = { sopa, principios, acompanamientos, updated_at: new Date().toISOString() };
  if (db) {
    try {
      return db.prepare(`
        UPDATE daily_specials 
        SET sopa = ?, principios = ?, acompanamientos = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
      `).run(sopa, JSON.stringify(principios), JSON.stringify(acompanamientos));
    } catch (e) {}
  }
  return true;
}

export function searchCustomers(query = '') {
  if (db) {
    try {
      if (!query || query.trim() === '') {
        return db.prepare('SELECT * FROM customers ORDER BY order_count DESC, id DESC LIMIT 15').all();
      }
      const q = `%${query.trim()}%`;
      return db.prepare(`
        SELECT * FROM customers 
        WHERE phone LIKE ? OR name LIKE ? OR address LIKE ?
        ORDER BY order_count DESC, id DESC LIMIT 20
      `).all(q, q, q);
    } catch (e) {}
  }
  const cleanQ = query.toLowerCase().trim();
  if (!cleanQ) return memCustomers.slice(0, 15);
  return memCustomers.filter(c => 
    c.phone.includes(cleanQ) || c.name.toLowerCase().includes(cleanQ) || c.address.toLowerCase().includes(cleanQ)
  );
}

export function getCustomerByPhone(phone) {
  const cleanPhone = phone.trim();
  if (db) {
    try {
      return db.prepare('SELECT * FROM customers WHERE phone = ?').get(cleanPhone);
    } catch (e) {}
  }
  return memCustomers.find(c => c.phone === cleanPhone) || null;
}

export function upsertCustomer({ name, phone, address, neighborhood = '', notes = '' }) {
  const cleanPhone = phone.trim();
  if (db) {
    try {
      const existing = getCustomerByPhone(cleanPhone);
      if (existing) {
        db.prepare(`
          UPDATE customers 
          SET name = ?, address = ?, neighborhood = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
          WHERE id = ?
        `).run(name, address, neighborhood, notes, existing.id);
        return db.prepare('SELECT * FROM customers WHERE id = ?').get(existing.id);
      } else {
        const res = db.prepare(`
          INSERT INTO customers (name, phone, address, neighborhood, notes, order_count)
          VALUES (?, ?, ?, ?, ?, 1)
        `).run(name, cleanPhone, address, neighborhood, notes);
        return db.prepare('SELECT * FROM customers WHERE id = ?').get(res.lastInsertRowid);
      }
    } catch (e) {}
  }

  let cust = memCustomers.find(c => c.phone === cleanPhone);
  if (cust) {
    cust.name = name;
    cust.address = address;
    cust.neighborhood = neighborhood;
    cust.notes = notes;
    cust.order_count = (cust.order_count || 1) + 1;
  } else {
    cust = {
      id: memCustomers.length + 1,
      name,
      phone: cleanPhone,
      address,
      neighborhood,
      notes,
      order_count: 1,
      created_at: new Date().toISOString()
    };
    memCustomers.push(cust);
  }
  return cust;
}

export function getActiveCashRegister() {
  if (db) {
    try {
      return db.prepare("SELECT * FROM cash_registers WHERE status = 'open' ORDER BY id DESC LIMIT 1").get();
    } catch (e) {}
  }
  return memCash.status === 'open' ? memCash : null;
}

export function openCashRegister(initialCash = 0, notes = '') {
  if (db) {
    try {
      const current = getActiveCashRegister();
      if (current) return current;
      const res = db.prepare(`
        INSERT INTO cash_registers (initial_cash, status, notes)
        VALUES (?, 'open', ?)
      `).run(initialCash, notes);
      return db.prepare('SELECT * FROM cash_registers WHERE id = ?').get(res.lastInsertRowid);
    } catch (e) {}
  }
  memCash = {
    id: (memCash.id || 1) + 1,
    opened_at: new Date().toISOString(),
    closed_at: null,
    initial_cash: initialCash,
    status: 'open',
    total_cash_sales: 0,
    total_nequi_sales: 0,
    total_daviplata_sales: 0,
    total_card_sales: 0,
    final_cash_counted: 0,
    cash_difference: 0,
    notes
  };
  return memCash;
}

export function closeCashRegister(id, finalCashCounted, notes = '') {
  if (db) {
    try {
      const reg = db.prepare('SELECT * FROM cash_registers WHERE id = ?').get(id);
      if (reg) {
        const expectedCash = (reg.initial_cash || 0) + (reg.total_cash_sales || 0);
        const diff = Number(finalCashCounted) - expectedCash;
        db.prepare(`
          UPDATE cash_registers 
          SET status = 'closed', closed_at = CURRENT_TIMESTAMP, 
              final_cash_counted = ?, cash_difference = ?, notes = ?
          WHERE id = ?
        `).run(finalCashCounted, diff, notes, id);
        return db.prepare('SELECT * FROM cash_registers WHERE id = ?').get(id);
      }
    } catch (e) {}
  }
  const expected = memCash.initial_cash + memCash.total_cash_sales;
  memCash.status = 'closed';
  memCash.closed_at = new Date().toISOString();
  memCash.final_cash_counted = finalCashCounted;
  memCash.cash_difference = finalCashCounted - expected;
  memCash.notes = notes;
  return memCash;
}

export function createOrder(orderData, items = []) {
  let customerId = orderData.customerId || null;
  if (orderData.orderType === 'domicilio' && orderData.customerPhone) {
    const cust = upsertCustomer({
      name: orderData.customerName || 'Cliente Domicilio',
      phone: orderData.customerPhone,
      address: orderData.deliveryAddress || '',
      neighborhood: orderData.deliveryNeighborhood || '',
      notes: orderData.deliveryNotes || ''
    });
    customerId = cust.id;
  }

  if (db) {
    try {
      const activeCash = getActiveCashRegister();
      const cashRegisterId = activeCash ? activeCash.id : null;

      const stmt = db.prepare(`
        INSERT INTO orders (
          order_type, table_number, customer_id, customer_name, customer_phone,
          delivery_address, delivery_neighborhood, delivery_notes,
          subtotal, delivery_fee, packaging_fee, total,
          payment_method, payment_change_for, status, cash_register_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      const res = stmt.run(
        orderData.orderType,
        orderData.tableNumber || '',
        customerId,
        orderData.customerName || '',
        orderData.customerPhone || '',
        orderData.deliveryAddress || '',
        orderData.deliveryNeighborhood || '',
        orderData.deliveryNotes || '',
        orderData.subtotal,
        orderData.deliveryFee || 0,
        orderData.packagingFee || 0,
        orderData.total,
        orderData.paymentMethod,
        orderData.paymentChangeFor || 0,
        orderData.status || 'completado',
        cashRegisterId
      );

      const orderId = res.lastInsertRowid;
      const itemStmt = db.prepare(`
        INSERT INTO order_items (order_id, product_name, price, quantity, notes)
        VALUES (?, ?, ?, ?, ?)
      `);

      for (const item of items) {
        itemStmt.run(orderId, item.name, item.price, item.quantity || 1, item.notes || '');
      }

      if (cashRegisterId) {
        const pay = orderData.paymentMethod.toLowerCase();
        const tot = Number(orderData.total);
        if (pay === 'efectivo') {
          db.prepare('UPDATE cash_registers SET total_cash_sales = total_cash_sales + ? WHERE id = ?').run(tot, cashRegisterId);
        } else if (pay === 'nequi') {
          db.prepare('UPDATE cash_registers SET total_nequi_sales = total_nequi_sales + ? WHERE id = ?').run(tot, cashRegisterId);
        } else if (pay === 'daviplata') {
          db.prepare('UPDATE cash_registers SET total_daviplata_sales = total_daviplata_sales + ? WHERE id = ?').run(tot, cashRegisterId);
        } else {
          db.prepare('UPDATE cash_registers SET total_card_sales = total_card_sales + ? WHERE id = ?').run(tot, cashRegisterId);
        }
      }

      return getOrderDetails(orderId);
    } catch (e) {}
  }

  // Memory fallback order
  const orderId = memOrders.length + 1;
  const newOrder = {
    id: orderId,
    ...orderData,
    items,
    created_at: new Date().toISOString()
  };
  memOrders.push(newOrder);

  const pay = orderData.paymentMethod?.toLowerCase() || 'efectivo';
  const tot = Number(orderData.total) || 0;
  if (pay === 'efectivo') memCash.total_cash_sales += tot;
  else if (pay === 'nequi') memCash.total_nequi_sales += tot;
  else if (pay === 'daviplata') memCash.total_daviplata_sales += tot;
  else memCash.total_card_sales += tot;

  return newOrder;
}

export function getOrderDetails(orderId) {
  if (db) {
    try {
      const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
      if (order) {
        const items = db.prepare('SELECT * FROM order_items WHERE order_id = ?').all(orderId);
        return { ...order, items };
      }
    } catch (e) {}
  }
  return memOrders.find(o => o.id === orderId) || null;
}

export function getRecentOrders(limit = 30) {
  if (db) {
    try {
      const orders = db.prepare(`
        SELECT o.*, 
          (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
        FROM orders o 
        ORDER BY o.id DESC 
        LIMIT ?
      `).all(limit);

      return orders.map(order => ({
        ...order,
        items: db.prepare('SELECT * FROM order_items WHERE order_id = ?').all(order.id)
      }));
    } catch (e) {}
  }
  return memOrders.slice(-limit).reverse();
}

export function recordView() {
  memViews += 1;
  if (db) {
    try {
      const today = new Date().toISOString().split('T')[0];
      db.prepare(`
        INSERT INTO views_counter (date, views_count) 
        VALUES (?, 1)
        ON CONFLICT(date) DO UPDATE SET views_count = views_count + 1
      `).run(today);
    } catch (e) {}
  }
}

export function getDashboardMetrics() {
  if (db) {
    try {
      const today = new Date().toISOString().split('T')[0];
      const todayOrders = db.prepare(`
        SELECT 
          COUNT(*) as count,
          COALESCE(SUM(total), 0) as total_sales,
          COALESCE(SUM(CASE WHEN payment_method = 'efectivo' THEN total ELSE 0 END), 0) as cash_sales,
          COALESCE(SUM(CASE WHEN payment_method = 'nequi' THEN total ELSE 0 END), 0) as nequi_sales,
          COALESCE(SUM(CASE WHEN payment_method = 'daviplata' THEN total ELSE 0 END), 0) as daviplata_sales,
          COALESCE(SUM(CASE WHEN payment_method = 'tarjeta' THEN total ELSE 0 END), 0) as card_sales
        FROM orders 
        WHERE date(created_at, 'localtime') = ?
      `).get(today);

      const topDishes = db.prepare(`
        SELECT product_name, SUM(quantity) as sold_count, SUM(price * quantity) as total_revenue
        FROM order_items
        GROUP BY product_name
        ORDER BY sold_count DESC
        LIMIT 6
      `).all();

      const totalCustomers = db.prepare('SELECT COUNT(*) as count FROM customers').get().count;
      const todayViews = db.prepare('SELECT views_count FROM views_counter WHERE date = ?').get(today)?.views_count || 0;
      const activeCash = getActiveCashRegister();

      return {
        todaySales: todayOrders.total_sales,
        todayOrderCount: todayOrders.count,
        cashSales: todayOrders.cash_sales,
        digitalSales: todayOrders.nequi_sales + todayOrders.daviplata_sales + todayOrders.card_sales,
        todayViews,
        totalCustomers,
        topDishes,
        activeCash
      };
    } catch (e) {}
  }

  const dishMap = new Map();
  for (const ord of memOrders) {
    for (const it of (ord.items || [])) {
      const name = it.name || it.product_name || 'Plato';
      const qty = Number(it.quantity || 1);
      const rev = Number(it.price || 0) * qty;
      const cur = dishMap.get(name) || { product_name: name, sold_count: 0, total_revenue: 0 };
      cur.sold_count += qty;
      cur.total_revenue += rev;
      dishMap.set(name, cur);
    }
  }
  const computedTopDishes = Array.from(dishMap.values())
    .sort((a, b) => b.sold_count - a.sold_count || b.total_revenue - a.total_revenue)
    .slice(0, 6);

  return {
    todaySales: memCash.total_cash_sales + memCash.total_nequi_sales + memCash.total_daviplata_sales + memCash.total_card_sales,
    todayOrderCount: memOrders.length,
    cashSales: memCash.total_cash_sales,
    digitalSales: memCash.total_nequi_sales + memCash.total_daviplata_sales + memCash.total_card_sales,
    todayViews: memViews,
    totalCustomers: memCustomers.length,
    topDishes: computedTopDishes,
    activeCash: memCash
  };
}

export { db };
export default db;

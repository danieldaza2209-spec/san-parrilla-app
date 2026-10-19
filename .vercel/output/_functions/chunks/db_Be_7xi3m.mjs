import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const require$1 = createRequire(import.meta.url);
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
const isVercel = Boolean(process.env.VERCEL || process.env.AWS_REGION || process.env.LAMBDA_TASK_ROOT);

// Categorías del Menú
const fallbackCategories = [
  { id: 'especiales_hoy', name: 'Especiales de Hoy', sort_order: 1 },
  { id: 'fuertes_165', name: 'Platos Fuertes $16.500', sort_order: 2 },
  { id: 'fuertes_175', name: 'Platos Fuertes $17.500', sort_order: 3 },
  { id: 'especiales_21', name: 'Especiales & Parrilladas', sort_order: 4 },
  { id: 'picadas', name: 'Picadas Especiales', sort_order: 5 },
  { id: 'bebidas', name: 'Bebidas y Adicionales', sort_order: 6 },
];

const fallbackDailySpecials = {
  sopa: 'Campesina',
  principios: ['Ensalada de atún', 'Garbanzos rancheros', 'Frijoles'],
  acompanamientos: ['Francesa casera', 'Torta de zanahoria', 'Tajadas maduras'],
  updated_at: new Date().toISOString()
};

const initialProductList = [
  // Plato de Prueba de Impresión Térmica SAT Q22
  { id: 'test-print-sat', name: '🔥 Combo Prueba Impresión SAT Q22', price: 1000, category_id: 'fuertes_165', description: 'Plato de prueba rápida para calibrar corte e impresión en impresora térmica SAT Q22 (80mm).', is_active: 1, is_featured: 1, sort_order: -999 },

  // 16.500
  { id: 't1-0', name: 'Milanesa de pollo', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 't1-1', name: 'Nuggets de pollo', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 't1-2', name: 'Pernil frito', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 't1-3', name: 'Pernil bbq', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 3 },
  { id: 't1-4', name: 'Lomo de cerdo a la plancha', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 4 },
  { id: 't1-5', name: 'Hígado en bistec', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 5 },
  { id: 't1-6', name: 'Lomo a la mostaza', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 6 },
  { id: 't1-7', name: 'Chuleta en salsa criolla', price: 16500, category_id: 'fuertes_165', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 7 },

  // 17.500
  { id: 't2-0', name: 'Carne a la plancha', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 't2-1', name: 'Carne bistec o bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 't2-2', name: 'Pechuga a la plancha', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 't2-3', name: 'Pechuga en salsa criolla', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 3 },
  { id: 't2-4', name: 'Pechuga apanada', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 4 },
  { id: 't2-5', name: 'Pechuga bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 5 },
  { id: 't2-6', name: 'Pernil hawaiano', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 6 },
  { id: 't2-7', name: 'Lomo de cerdo a la bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 7 },
  { id: 't2-8', name: 'Lomo de cerdo al ajillo', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 8 },
  { id: 't2-9', name: 'Chuleta de cerdo al ajillo', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 9 },
  { id: 't2-10', name: 'Chuleta de cerdo a la bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 10 },
  { id: 't2-11', name: 'Bandeja paisa', price: 17500, category_id: 'fuertes_175', description: 'Plato típico tradicional con carne, chicharrón, huevo, arroz y frijol.', is_active: 1, is_featured: 1, sort_order: 11 },
  { id: 't2-12', name: 'Alitas bbq', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 12 },
  { id: 't2-13', name: 'Creps de pollo', price: 17500, category_id: 'fuertes_175', description: 'Incluye sopa del día, principio y acompañamiento a elección.', is_active: 1, is_featured: 0, sort_order: 13 },
  { id: 't2-14', name: 'Bistec a caballo', price: 17500, category_id: 'fuertes_175', description: 'Carne en salsa criolla coronada con huevo frito.', is_active: 1, is_featured: 0, sort_order: 14 },
  { id: 't2-15', name: 'Pechuga hawaiana', price: 17500, category_id: 'fuertes_175', description: 'Pechuga gratinada con piña caramelizada y queso.', is_active: 1, is_featured: 0, sort_order: 15 },
  { id: 't2-16', name: 'Arroz paisa', price: 17500, category_id: 'fuertes_175', description: 'Arroz salteado con chicharrón, plátano maduro y carnes.', is_active: 1, is_featured: 0, sort_order: 16 },
  { id: 't2-17', name: 'Combo Personal', price: 17500, category_id: 'fuertes_175', description: 'Opción rápida del asador.', is_active: 1, is_featured: 0, sort_order: 17 },
  { id: 't2-18', name: 'Arroz mixto', price: 17500, category_id: 'fuertes_175', description: 'Arroz frito con variedad de carnes y verduras frescas.', is_active: 1, is_featured: 0, sort_order: 18 },

  // Especiales & Brasas
  { id: 'esp-0', name: 'Sobrebarriga dorada', price: 21000, category_id: 'especiales_21', description: 'Corte suave y dorado a las brasas.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 'esp-1', name: 'Bagre frito', price: 21000, category_id: 'especiales_21', description: 'Pescado fresco del día con patacón.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 'esp-2', name: 'Bagre al ajillo', price: 21000, category_id: 'especiales_21', description: 'Bañado en reducción cremosa de ajo y finas hierbas.', is_active: 1, is_featured: 0, sort_order: 2 },
  { id: 'esp-3', name: 'Róbalo apanado', price: 21000, category_id: 'especiales_21', description: 'Filete de róbalo crocante.', is_active: 1, is_featured: 0, sort_order: 3 },
  { id: 'esp-4', name: 'Róbalo al ajillo', price: 21000, category_id: 'especiales_21', description: 'Filete bañado en salsa de ajillo.', is_active: 1, is_featured: 0, sort_order: 4 },
  { id: 'esp-5', name: 'Bagre sudado', price: 21000, category_id: 'especiales_21', description: 'En jugo natural de tomate criollo y cebolla.', is_active: 1, is_featured: 0, sort_order: 5 },
  { id: 'esp-6', name: 'Mojarra frita', price: 21000, category_id: 'especiales_21', description: 'Mojarra entera frita bien crocante con patacones.', is_active: 1, is_featured: 0, sort_order: 6 },
  { id: 'esp-7', name: 'Costillas bbq', price: 23000, category_id: 'especiales_21', description: 'Costillas ahumadas bañadas en salsa BBQ casera.', is_active: 1, is_featured: 0, sort_order: 7 },
  { id: 'esp-8', name: 'Pechuga con maíz gratinada', price: 23000, category_id: 'especiales_21', description: 'Pechuga a la plancha con crema de maíz y queso gratinado.', is_active: 1, is_featured: 0, sort_order: 8 },
  { id: 'esp-9', name: 'Pechuga en champiñones', price: 23000, category_id: 'especiales_21', description: 'Filete de pechuga con salsa cremosa de champiñones.', is_active: 1, is_featured: 0, sort_order: 9 },
  { id: 'esp-10', name: 'Churrasco', price: 25000, category_id: 'especiales_21', description: 'Corte de res jugoso asado al carbón.', is_active: 1, is_featured: 1, sort_order: 10 },
  { id: 'esp-11', name: 'Parrillada', price: 25000, category_id: 'especiales_21', description: 'Combinación de carnes a la parrilla con papa salada y arepa.', is_active: 1, is_featured: 1, sort_order: 11 },
  { id: 'esp-12', name: 'Pechuga gratinada con tocineta y champiñones', price: 25000, category_id: 'especiales_21', description: 'Especialidad de la casa.', is_active: 1, is_featured: 0, sort_order: 12 },
  { id: 'esp-13', name: 'Pollo Santo domingo', price: 25000, category_id: 'especiales_21', description: 'Receta tradicional San Parrilla.', is_active: 1, is_featured: 0, sort_order: 13 },
  { id: 'esp-14', name: 'Llanera mixta', price: 27000, category_id: 'especiales_21', description: 'Carne a la llanera con chunchullo y plátano.', is_active: 1, is_featured: 0, sort_order: 14 },
  { id: 'esp-15', name: 'Parrilla mixta', price: 27000, category_id: 'especiales_21', description: 'Res, cerdo y pollo a las brasas.', is_active: 1, is_featured: 1, sort_order: 15 },
  { id: 'esp-16', name: 'Carne grande', price: 27000, category_id: 'especiales_21', description: 'Porción generosa de carne asada para buen apetito.', is_active: 1, is_featured: 0, sort_order: 16 },
  { id: 'esp-17', name: 'Pechuga grande', price: 27000, category_id: 'especiales_21', description: 'Doble pechuga a la plancha.', is_active: 1, is_featured: 0, sort_order: 17 },
  { id: 'esp-18', name: 'Cazuela de mariscos', price: 29000, category_id: 'especiales_21', description: 'Cremosa y cargada de mariscos frescos.', is_active: 1, is_featured: 1, sort_order: 18 },
  { id: 'esp-19', name: 'Róbalo a la marinera', price: 29000, category_id: 'especiales_21', description: 'Filete coronado con mariscos en salsa.', is_active: 1, is_featured: 0, sort_order: 19 },
  { id: 'esp-20', name: 'Bagre a la marinera', price: 29000, category_id: 'especiales_21', description: 'Bagre bañado en salsa marinera.', is_active: 1, is_featured: 0, sort_order: 20 },
  { id: 'esp-21', name: 'Róbalo con camarones', price: 29000, category_id: 'especiales_21', description: 'Exquisito filete con camarones salteados.', is_active: 1, is_featured: 0, sort_order: 21 },

  // Picadas
  { id: 'pic-1', name: 'Picada x 1', price: 27500, category_id: 'picadas', description: 'Variedad de carnes y acompañamiento para una persona.', is_active: 1, is_featured: 0, sort_order: 0 },
  { id: 'pic-2', name: 'Picada x 2', price: 50000, category_id: 'picadas', description: 'Perfecta para compartir en pareja. Incluye carnes, chorizo y papas.', is_active: 1, is_featured: 0, sort_order: 1 },
  { id: 'pic-3', name: 'Picada x 3', price: 66000, category_id: 'picadas', description: 'Gran porción familiar para tres personas.', is_active: 1, is_featured: 0, sort_order: 2 },
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

let db = null;

// Initialize SQLite only in non-serverless local environments
if (!isVercel) {
  try {
    const modName = 'node' + ':sqlite';
    const sqlite = require$1(modName);
    if (sqlite && sqlite.DatabaseSync) {
      const dataDir = path.resolve(__dirname$1, '../../data');
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
        const catCount = db.prepare('SELECT count(*) as count FROM categories').get().count;
        if (catCount === 0) {
          const insertCat = db.prepare('INSERT INTO categories (id, name, sort_order) VALUES (?, ?, ?)');
          for (const c of fallbackCategories) {
            insertCat.run(c.id, c.name, c.sort_order);
          }
        }
        const prodCount = db.prepare('SELECT count(*) as count FROM products').get().count;
        if (prodCount === 0) {
          const insertProd = db.prepare(`
            INSERT INTO products (id, name, price, category_id, description, is_active, is_featured, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          `);
          for (const p of initialProductList) {
            insertProd.run(p.id, p.name, p.price, p.category_id, p.description || '', p.is_active, p.is_featured, p.sort_order);
          }
        }
        // Always ensure test product is available
        const hasTest = db.prepare("SELECT count(*) as count FROM products WHERE id = 'test-print-sat'").get().count;
        if (hasTest === 0) {
          db.prepare(`
            INSERT OR REPLACE INTO products (id, name, price, category_id, description, is_active, is_featured, sort_order)
            VALUES ('test-print-sat', '🔥 Combo Prueba Impresión SAT Q22', 1000, 'fuertes_165', 'Plato de prueba rápida para calibrar corte e impresión en impresora térmica SAT Q22 (80mm).', 1, 1, -999)
          `).run();
        }
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

function getCategories() {
  if (db) {
    try {
      const rows = db.prepare('SELECT * FROM categories ORDER BY sort_order ASC').all();
      if (rows && rows.length > 0) return rows;
    } catch (e) {}
  }
  return fallbackCategories;
}

function getProducts(onlyActive = true) {
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
const INTERNAL_PRODUCT_IDS = new Set(['test-print-sat']);

function getPublicProducts() {
  const rows = getProducts(true) || [];
  const visible = rows.filter((p) => !INTERNAL_PRODUCT_IDS.has(p.id));
  return visible.length > 0 ? visible : initialProductList.filter((p) => !INTERNAL_PRODUCT_IDS.has(p.id));
}

function getDailySpecials() {
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

function updateDailySpecials(sopa, principios, acompanamientos) {
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

function searchCustomers(query = '') {
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

function getCustomerByPhone(phone) {
  const cleanPhone = phone.trim();
  if (db) {
    try {
      return db.prepare('SELECT * FROM customers WHERE phone = ?').get(cleanPhone);
    } catch (e) {}
  }
  return memCustomers.find(c => c.phone === cleanPhone) || null;
}

function upsertCustomer({ name, phone, address, neighborhood = '', notes = '' }) {
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

function getActiveCashRegister() {
  if (db) {
    try {
      return db.prepare("SELECT * FROM cash_registers WHERE status = 'open' ORDER BY id DESC LIMIT 1").get();
    } catch (e) {}
  }
  return memCash.status === 'open' ? memCash : null;
}

function openCashRegister(initialCash = 0, notes = '') {
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

function closeCashRegister(id, finalCashCounted, notes = '') {
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

function createOrder(orderData, items = []) {
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

function getOrderDetails(orderId) {
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

function getRecentOrders(limit = 30) {
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

function getDashboardMetrics() {
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

  return {
    todaySales: memCash.total_cash_sales + memCash.total_nequi_sales + memCash.total_daviplata_sales + memCash.total_card_sales,
    todayOrderCount: memOrders.length,
    cashSales: memCash.total_cash_sales,
    digitalSales: memCash.total_nequi_sales + memCash.total_daviplata_sales + memCash.total_card_sales,
    todayViews: memViews,
    totalCustomers: memCustomers.length,
    topDishes: [
      { product_name: 'Parrillada', sold_count: 14, total_revenue: 350000 },
      { product_name: 'Churrasco', sold_count: 11, total_revenue: 275000 },
      { product_name: 'Picada Berraca', sold_count: 8, total_revenue: 440000 }
    ],
    activeCash: memCash
  };
}
const db$1 = db;

export { getDailySpecials as a, getProducts as b, getCategories as c, getActiveCashRegister as d, closeCashRegister as e, getCustomerByPhone as f, getDashboardMetrics as g, getOrderDetails as h, getRecentOrders as i, createOrder as j, getPublicProducts as k, db$1 as l, updateDailySpecials as m, db as n, openCashRegister as o, fallbackCategories as p, fallbackDailySpecials as q, initialProductList as r, searchCustomers as s, upsertCustomer as u };

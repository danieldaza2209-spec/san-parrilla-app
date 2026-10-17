import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.resolve(__dirname$1, '../../data');

if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const dbPath = path.join(dataDir, 'sanparrilla.db');
const db = new DatabaseSync(dbPath);

// Enable WAL mode and foreign keys for high performance and reliability
db.exec('PRAGMA journal_mode = WAL;');
db.exec('PRAGMA foreign_keys = ON;');

// Initialize Tables
db.exec(`
  CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
  );

  CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    category_id TEXT NOT NULL,
    description TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    is_featured INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(id)
  );

  CREATE TABLE IF NOT EXISTS daily_specials (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    sopa TEXT NOT NULL,
    principios TEXT NOT NULL,
    acompanamientos TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL,
    neighborhood TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    order_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS cash_registers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    initial_cash INTEGER NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'open', -- 'open' or 'closed'
    total_cash_sales INTEGER DEFAULT 0,
    total_nequi_sales INTEGER DEFAULT 0,
    total_daviplata_sales INTEGER DEFAULT 0,
    total_card_sales INTEGER DEFAULT 0,
    final_cash_counted INTEGER DEFAULT 0,
    cash_difference INTEGER DEFAULT 0,
    notes TEXT DEFAULT ''
  );

  CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_type TEXT NOT NULL, -- 'mesa', 'domicilio', 'para_llevar'
    table_number TEXT,
    customer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    delivery_address TEXT,
    delivery_neighborhood TEXT,
    delivery_notes TEXT,
    subtotal INTEGER NOT NULL,
    delivery_fee INTEGER DEFAULT 0,
    packaging_fee INTEGER DEFAULT 0,
    total INTEGER NOT NULL,
    payment_method TEXT NOT NULL, -- 'efectivo', 'nequi', 'daviplata', 'tarjeta'
    payment_change_for INTEGER DEFAULT 0,
    status TEXT DEFAULT 'completado', -- 'pendiente', 'preparando', 'en_camino', 'completado', 'cancelado'
    cash_register_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (cash_register_id) REFERENCES cash_registers(id)
  );

  CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    price INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    notes TEXT DEFAULT '',
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS views_counter (
    date TEXT PRIMARY KEY,
    views_count INTEGER DEFAULT 0
  );
`);

// Seed Categories & Initial Products if empty
function seedDatabase() {
  const catCount = db.prepare('SELECT count(*) as count FROM categories').get().count;
  if (catCount === 0) {
    const insertCat = db.prepare('INSERT INTO categories (id, name, sort_order) VALUES (?, ?, ?)');
    insertCat.run('especiales_hoy', 'Especiales de Hoy', 1);
    insertCat.run('fuertes_165', 'Platos Fuertes $16.500', 2);
    insertCat.run('fuertes_175', 'Platos Fuertes $17.500', 3);
    insertCat.run('especiales_21', 'Especiales & Parrilladas', 4);
    insertCat.run('picadas', 'Picadas Especiales', 5);
    insertCat.run('bebidas', 'Bebidas y Adicionales', 6);
  }

  const prodCount = db.prepare('SELECT count(*) as count FROM products').get().count;
  if (prodCount === 0) {
    const insertProd = db.prepare(
      'INSERT INTO products (id, name, price, category_id, description, is_active, is_featured, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    );

    // Tier 1: 16.500
    const tier165 = [
      'Milanesa de pollo', 'Nuggets de pollo', 'Pernil frito', 'Pernil bbq',
      'Lomo de cerdo a la plancha', 'Hígado en bistec', 'Lomo a la mostaza', 'Chuleta en salsa criolla'
    ];
    tier165.forEach((name, i) => {
      insertProd.run(`t1-${i}`, name, 16500, 'fuertes_165', 'Incluye sopa del día, principio y acompañamiento a elección.', 1, 0, i);
    });

    // Tier 2: 17.500
    const tier175 = [
      'Carne a la plancha', 'Carne bistec o bbq', 'Pechuga a la plancha', 'Pechuga en salsa criolla',
      'Pechuga apanada', 'Pechuga bbq', 'Pernil hawaiano', 'Lomo de cerdo a la bbq',
      'Lomo de cerdo al ajillo', 'Chuleta de cerdo al ajillo', 'Chuleta de cerdo a la bbq',
      'Bandeja paisa', 'Alitas bbq', 'Creps de pollo', 'Bistec a caballo', 'Pechuga hawaiana',
      'Arroz paisa', 'Combo Personal', 'Arroz mixto'
    ];
    tier175.forEach((name, i) => {
      insertProd.run(`t2-${i}`, name, 17500, 'fuertes_175', 'Incluye sopa del día, principio y acompañamiento a elección.', 1, name === 'Bandeja paisa' ? 1 : 0, i);
    });

    // Especiales & Parrilla
    const espList = [
      { name: 'Sobrebarriga dorada', price: 21000 },
      { name: 'Bagre frito', price: 21000 },
      { name: 'Bagre al ajillo', price: 21000 },
      { name: 'Róbalo apanado', price: 21000 },
      { name: 'Róbalo al ajillo', price: 21000 },
      { name: 'Bagre sudado', price: 21000 },
      { name: 'Mojarra frita', price: 21000 },
      { name: 'Costillas bbq', price: 23000 },
      { name: 'Pechuga con maíz gratinada', price: 23000 },
      { name: 'Pechuga en champiñones', price: 23000 },
      { name: 'Churrasco', price: 25000, featured: 1 },
      { name: 'Parrillada', price: 25000, featured: 1 },
      { name: 'Pechuga gratinada con tocineta y champiñones', price: 25000 },
      { name: 'Pollo Santo domingo', price: 25000 },
      { name: 'Llanera mixta', price: 27000 },
      { name: 'Parrilla mixta', price: 27000, featured: 1 },
      { name: 'Carne grande', price: 27000 },
      { name: 'Pechuga grande', price: 27000 },
      { name: 'Cazuela de mariscos', price: 29000, featured: 1 },
      { name: 'Róbalo a la marinera', price: 29000 },
      { name: 'Bagre a la marinera', price: 29000 },
      { name: 'Róbalo con camarones', price: 29000 },
    ];
    espList.forEach((item, i) => {
      insertProd.run(`esp-${i}`, item.name, item.price, 'especiales_21', 'Corte seleccionado a las brasas con acompañamiento.', 1, item.featured ? 1 : 0, i);
    });

    // Picadas
    const picadas = [
      { id: 'pic-1', name: 'Picada x 1', price: 27500, desc: 'Variedad de carnes y acompañamiento para una persona.' },
      { id: 'pic-2', name: 'Picada x 2', price: 50000, desc: 'Perfecta para compartir en pareja. Incluye carnes, chorizo y papas.' },
      { id: 'pic-3', name: 'Picada x 3', price: 66000, desc: 'Gran porción familiar para tres personas.' },
      { id: 'pic-4', name: 'Picada Berraca', price: 55000, desc: 'Chicharrón crujiente, costilla, lomo y papitas criollas.', feat: 1 },
    ];
    picadas.forEach((p, i) => {
      insertProd.run(p.id, p.name, p.price, 'picadas', p.desc, 1, p.feat ? 1 : 0, i);
    });

    // Bebidas y Adicionales
    const bebidas = [
      { id: 'beb-1', name: 'Gaseosa 400ml', price: 4000 },
      { id: 'beb-2', name: 'Gaseosa 1.5L', price: 8000 },
      { id: 'beb-3', name: 'Jugo Natural en Agua', price: 6000 },
      { id: 'beb-4', name: 'Jugo Natural en Leche', price: 7500 },
      { id: 'beb-5', name: 'Cerveza Club Colombia / Águila', price: 5500 },
      { id: 'beb-6', name: 'Porción de Papas a la Francesa', price: 6000 },
      { id: 'beb-7', name: 'Porción de Patacón con Hogao', price: 6500 },
    ];
    bebidas.forEach((b, i) => {
      insertProd.run(b.id, b.name, b.price, 'bebidas', '', 1, 0, i);
    });
  }

  // Seed Daily Specials
  const specialCount = db.prepare('SELECT count(*) as count FROM daily_specials').get().count;
  if (specialCount === 0) {
    db.prepare(`
      INSERT INTO daily_specials (id, sopa, principios, acompanamientos)
      VALUES (1, ?, ?, ?)
    `).run(
      'Campesina',
      JSON.stringify(['Ensalada de atún', 'Garbanzos rancheros', 'Frijoles']),
      JSON.stringify(['Francesa casera', 'Torta de zanahoria', 'Tajadas maduras'])
    );
  }

  // Seed sample active cash register if none exists
  const cashCount = db.prepare('SELECT count(*) as count FROM cash_registers').get().count;
  if (cashCount === 0) {
    db.prepare(`
      INSERT INTO cash_registers (initial_cash, status, notes)
      VALUES (100000, 'open', 'Apertura inicial de caja')
    `).run();
  }
}

seedDatabase();

// ==========================================
// EXPORTED DB HELPER FUNCTIONS
// ==========================================

function getCategories() {
  return db.prepare('SELECT * FROM categories ORDER BY sort_order ASC').all();
}

function getProducts(onlyActive = true) {
  if (onlyActive) {
    return db.prepare('SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order ASC').all();
  }
  return db.prepare('SELECT * FROM products ORDER BY category_id, sort_order ASC').all();
}

function getDailySpecials() {
  const row = db.prepare('SELECT * FROM daily_specials WHERE id = 1').get();
  if (!row) return null;
  return {
    sopa: row.sopa,
    principios: JSON.parse(row.principios || '[]'),
    acompanamientos: JSON.parse(row.acompanamientos || '[]'),
    updated_at: row.updated_at
  };
}

function updateDailySpecials(sopa, principios, acompanamientos) {
  return db.prepare(`
    UPDATE daily_specials 
    SET sopa = ?, principios = ?, acompanamientos = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
  `).run(sopa, JSON.stringify(principios), JSON.stringify(acompanamientos));
}

// Customers & Delivery
function searchCustomers(query = '') {
  if (!query || query.trim() === '') {
    return db.prepare('SELECT * FROM customers ORDER BY order_count DESC, id DESC LIMIT 15').all();
  }
  const q = `%${query.trim()}%`;
  return db.prepare(`
    SELECT * FROM customers 
    WHERE phone LIKE ? OR name LIKE ? OR address LIKE ?
    ORDER BY order_count DESC, id DESC LIMIT 20
  `).all(q, q, q);
}

function getCustomerByPhone(phone) {
  const cleanPhone = phone.trim();
  return db.prepare('SELECT * FROM customers WHERE phone = ?').get(cleanPhone);
}

function upsertCustomer({ name, phone, address, neighborhood = '', notes = '' }) {
  const cleanPhone = phone.trim();
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
}

// Cash Register (Caja)
function getActiveCashRegister() {
  return db.prepare("SELECT * FROM cash_registers WHERE status = 'open' ORDER BY id DESC LIMIT 1").get();
}

function openCashRegister(initialCash = 0, notes = '') {
  const current = getActiveCashRegister();
  if (current) return current;
  const res = db.prepare(`
    INSERT INTO cash_registers (initial_cash, status, notes)
    VALUES (?, 'open', ?)
  `).run(initialCash, notes);
  return db.prepare('SELECT * FROM cash_registers WHERE id = ?').get(res.lastInsertRowid);
}

function closeCashRegister(id, finalCashCounted, notes = '') {
  const reg = db.prepare('SELECT * FROM cash_registers WHERE id = ?').get(id);
  if (!reg) throw new Error('Caja no encontrada');
  
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

// Orders & POS
function createOrder(orderData, items = []) {
  const activeCash = getActiveCashRegister();
  const cashRegisterId = activeCash ? activeCash.id : null;

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
    // increment order count
    db.prepare('UPDATE customers SET order_count = order_count + 1 WHERE id = ?').run(customerId);
  }

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

  // Update cash register totals
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
}

function getOrderDetails(orderId) {
  const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
  if (!order) return null;
  const items = db.prepare('SELECT * FROM order_items WHERE order_id = ?').all(orderId);
  return { ...order, items };
}

function getRecentOrders(limit = 30) {
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
}

// Analytics
function recordView() {
  const today = new Date().toISOString().split('T')[0];
  db.prepare(`
    INSERT INTO views_counter (date, views_count) 
    VALUES (?, 1)
    ON CONFLICT(date) DO UPDATE SET views_count = views_count + 1
  `).run(today);
}

function getDashboardMetrics() {
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
}

export { getDailySpecials as a, getProducts as b, getCategories as c, getActiveCashRegister as d, closeCashRegister as e, getCustomerByPhone as f, getDashboardMetrics as g, getOrderDetails as h, getRecentOrders as i, createOrder as j, db as k, updateDailySpecials as l, openCashRegister as o, recordView as r, searchCustomers as s, upsertCustomer as u };

#!/usr/bin/env node
/**
 * Script d'insertion de commande de test dans Supabase
 * Utilisation: node test_insert.js
 * Assure-toi d'avoir installé: npm install @supabase/supabase-js dotenv
 */

// Chargement des variables d'environnement
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('❌ Variables SUPABASE_URL ou SUPABASE_KEY manquantes.');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

function randomItem() {
  const ramenTypes = ['Ramen Miso', 'Ramen Shoyu', 'Ramen Tonkotsu', 'Ramen Vegan'];
  const optionsPool = ['Extra chashu', 'Sans oignons', 'Œuf mariné', 'Piment lvl 3'];
  const name = ramenTypes[Math.floor(Math.random() * ramenTypes.length)];
  const quantity = 1 + Math.floor(Math.random() * 3);
  const priceMap = { 'Ramen Miso': 12.5, 'Ramen Shoyu': 11.5, 'Ramen Tonkotsu': 13.5, 'Ramen Vegan': 12.0 };
  const optCount = Math.floor(Math.random() * 3);
  const chosen = [];
  for (let i = 0; i < optCount; i++) {
    chosen.push(optionsPool[Math.floor(Math.random() * optionsPool.length)]);
  }
  return {
    name,
    quantity,
    price: priceMap[name] || 10,
    options: chosen,
    comment: Math.random() < 0.3 ? 'Bien chaud SVP' : null
  };
}

async function run() {
  const orderNumber = 'TEST-' + Date.now();
  const items = [randomItem(), randomItem()];

  const payload = {
    order_number: orderNumber,
    status: 'pending_print',
    customer_name: 'Client Test Ubuntu',
    customer_phone: '0600000000',
    payment_status: Math.random() < 0.5 ? 'paid' : 'pending',
    items,
  };

  console.log('🧪 Insertion commande de test:', payload.order_number);
  const { error } = await supabase.from('orders').insert(payload);

  if (error) {
    console.error('❌ Erreur insertion:', error);
    process.exit(1);
  }
  console.log('✅ Commande insérée avec statut pending_print');
  console.log('🎯 Surveille le terminal du script Python pour le ticket.');
}

run().catch(e => {
  console.error('❌ Exception:', e);
  process.exit(1);
});

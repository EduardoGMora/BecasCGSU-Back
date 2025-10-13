"use client";

import { useState, FormEvent } from 'react';
import styles from './becas.module.css';

// Tipo para definir la estructura de una beca
interface Beca {
  id: number;
  nombre: string;
  descripcion: string;
  monto: number;
}

// Datos iniciales de ejemplo
const becasIniciales: Beca[] = [
  { id: 1, nombre: 'Beca de Excelencia Académica', descripcion: 'Para estudiantes con promedio superior a 9.5', monto: 5000 },
  { id: 2, nombre: 'Beca Deportiva', descripcion: 'Para atletas destacados en competencias nacionales', monto: 3500 },
  { id: 3, nombre: 'Beca de Apoyo Económico', descripcion: 'Para estudiantes con necesidad económica comprobable', monto: 2000 },
];

export default function BecasPage() {
  const [becas, setBecas] = useState(becasIniciales);
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');

  const handleAddBeca = (e: FormEvent) => {
    e.preventDefault();
    if (!nombre || !descripcion) return;

    const nuevaBeca: Beca = {
      id: Date.now(), // ID simple basado en la fecha actual
      nombre,
      descripcion,
      monto: Math.floor(Math.random() * 5000) + 1000, // Monto aleatorio para el ejemplo
    };

    // Aquí es donde en el futuro llamarías a tu API para guardar en la BD
    setBecas([...becas, nuevaBeca]);

    // Limpiar el formulario
    setNombre('');
    setDescripcion('');
  };

  return (
    <div>
      <h1>Gestión de Becas</h1>

      {/* Formulario para agregar becas */}
      <form onSubmit={handleAddBeca} className={styles.form}>
        <h3>Agregar Nueva Beca</h3>
        <input
          type="text"
          placeholder="Nombre de la beca"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          className={styles.input}
          required
        />
        <textarea
          placeholder="Descripción de la beca"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          className={styles.textarea}
          required
        />
        <button type="submit" className={styles.button}>
          Agregar Beca
        </button>
      </form>

      {/* Lista de becas existentes */}
      <div className={styles.becasList}>
        {becas.map((beca) => (
          <div key={beca.id} className={styles.becaCard}>
            <h3>{beca.nombre}</h3>
            <p>{beca.descripcion}</p>
            <span className={styles.monto}>Monto: ${beca.monto.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
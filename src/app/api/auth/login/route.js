import { prisma } from '@/lib/prisma';
import { NextResponse } from 'next/server';
import bcrypt from 'bcrypt';

export async function POST(request) {
  try {
    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { message: 'Email y contraseña son requeridos.' },
        { status: 400 }
      );
    }
    
    // Usamos la instancia 'prisma' importada
    // OJO: El modelo se usa en minúscula ('user'), no 'User'.
    const user = await prisma.user.findUnique({
      where: {
        email: email,
      },
    });

    if (!user) {
      return NextResponse.json(
        { message: 'Credenciales inválidas.' },
        { status: 401 }
      );
    }

    const isPasswordValid = await bcrypt.compare(password, user.contraseña);

    if (!isPasswordValid) {
      return NextResponse.json(
        { message: 'Credenciales inválidas.' },
        { status: 401 }
      );
    }
    
    const { contraseña: _, ...userWithoutPassword } = user;

    return NextResponse.json({
      message: 'Login exitoso',
      user: userWithoutPassword,
    });

  } catch (error) {
    console.error("Error en la API de login:", error);
    return NextResponse.json(
      { message: 'Ocurrió un error en el servidor.' },
      { status: 500 }
    );
  }
}
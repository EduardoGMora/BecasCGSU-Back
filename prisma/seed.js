const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcrypt');

const prisma = new PrismaClient();

async function main() {
  console.log('Iniciando el script de seeding...');

  // --- DATOS DEL USUARIO DE PRUEBA ---
  const plainPassword = '123';
  const saltRounds = 10;
  const hashedPassword = await bcrypt.hash(plainPassword, saltRounds);
  console.log('Contraseña encriptada con éxito.');

  // Usar el modelo User y los campos correctos
  const user = await prisma.User.create({
    data: {
      email: 'usuario@correo.com',
      nombre: 'usuario',
      contraseña: hashedPassword,
      // Las fechas se generan automáticamente
    },
  });

  console.log(`Usuario de prueba creado con éxito:`);
  console.log(user);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
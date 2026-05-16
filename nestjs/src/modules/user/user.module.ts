import { Module } from '@nestjs/common';
import { ClientModule } from 'src/modules/client/client.module';
import { UserService } from './user.service';

@Module({
  imports: [ClientModule],
  controllers: [],
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}

drop extension if exists "pg_net";


  create table "public"."applications" (
    "id" uuid not null default gen_random_uuid(),
    "student_id" uuid,
    "scholarship_id" uuid,
    "status" text default 'Recibida'::text,
    "submitted_at" timestamp with time zone default now()
      );


alter table "public"."applications" enable row level security;


  create table "public"."profiles" (
    "id" uuid not null,
    "university_center_id" uuid,
    "full_name" text,
    "student_code" text,
    "gpa" numeric,
    "email" text,
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."profiles" enable row level security;


  create table "public"."scholarship_types" (
    "id" uuid not null default gen_random_uuid(),
    "name" text not null,
    "description" text,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."scholarship_types" enable row level security;


  create table "public"."scholarships" (
    "id" uuid not null default gen_random_uuid(),
    "university_center_id" uuid,
    "scholarship_type_id" uuid,
    "title" text not null,
    "description" text,
    "requirements" jsonb,
    "application_start_date" timestamp with time zone,
    "application_end_date" timestamp with time zone,
    "status" text default 'Cerrada'::text,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."scholarships" enable row level security;


  create table "public"."university_centers" (
    "id" uuid not null default gen_random_uuid(),
    "name" text not null,
    "acronym" text,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."university_centers" enable row level security;

CREATE UNIQUE INDEX applications_pkey ON public.applications USING btree (id);

CREATE UNIQUE INDEX applications_student_id_scholarship_id_key ON public.applications USING btree (student_id, scholarship_id);

CREATE UNIQUE INDEX profiles_pkey ON public.profiles USING btree (id);

CREATE UNIQUE INDEX profiles_student_code_key ON public.profiles USING btree (student_code);

CREATE UNIQUE INDEX scholarship_types_pkey ON public.scholarship_types USING btree (id);

CREATE UNIQUE INDEX scholarships_pkey ON public.scholarships USING btree (id);

CREATE UNIQUE INDEX university_centers_pkey ON public.university_centers USING btree (id);

alter table "public"."applications" add constraint "applications_pkey" PRIMARY KEY using index "applications_pkey";

alter table "public"."profiles" add constraint "profiles_pkey" PRIMARY KEY using index "profiles_pkey";

alter table "public"."scholarship_types" add constraint "scholarship_types_pkey" PRIMARY KEY using index "scholarship_types_pkey";

alter table "public"."scholarships" add constraint "scholarships_pkey" PRIMARY KEY using index "scholarships_pkey";

alter table "public"."university_centers" add constraint "university_centers_pkey" PRIMARY KEY using index "university_centers_pkey";

alter table "public"."applications" add constraint "applications_scholarship_id_fkey" FOREIGN KEY (scholarship_id) REFERENCES public.scholarships(id) ON DELETE CASCADE not valid;

alter table "public"."applications" validate constraint "applications_scholarship_id_fkey";

alter table "public"."applications" add constraint "applications_student_id_fkey" FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE not valid;

alter table "public"."applications" validate constraint "applications_student_id_fkey";

alter table "public"."applications" add constraint "applications_student_id_scholarship_id_key" UNIQUE using index "applications_student_id_scholarship_id_key";

alter table "public"."profiles" add constraint "profiles_id_fkey" FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."profiles" validate constraint "profiles_id_fkey";

alter table "public"."profiles" add constraint "profiles_student_code_key" UNIQUE using index "profiles_student_code_key";

alter table "public"."profiles" add constraint "profiles_university_center_id_fkey" FOREIGN KEY (university_center_id) REFERENCES public.university_centers(id) not valid;

alter table "public"."profiles" validate constraint "profiles_university_center_id_fkey";

alter table "public"."scholarships" add constraint "scholarships_scholarship_type_id_fkey" FOREIGN KEY (scholarship_type_id) REFERENCES public.scholarship_types(id) not valid;

alter table "public"."scholarships" validate constraint "scholarships_scholarship_type_id_fkey";

alter table "public"."scholarships" add constraint "scholarships_university_center_id_fkey" FOREIGN KEY (university_center_id) REFERENCES public.university_centers(id) not valid;

alter table "public"."scholarships" validate constraint "scholarships_university_center_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  -- Inserta un nuevo registro en la tabla 'profiles'
  -- con el id y email del nuevo usuario de 'auth.users'
  INSERT INTO public.profiles (id, email)
  VALUES (new.id, new.email);
  RETURN new;
END;
$function$
;

grant delete on table "public"."applications" to "anon";

grant insert on table "public"."applications" to "anon";

grant references on table "public"."applications" to "anon";

grant select on table "public"."applications" to "anon";

grant trigger on table "public"."applications" to "anon";

grant truncate on table "public"."applications" to "anon";

grant update on table "public"."applications" to "anon";

grant delete on table "public"."applications" to "authenticated";

grant insert on table "public"."applications" to "authenticated";

grant references on table "public"."applications" to "authenticated";

grant select on table "public"."applications" to "authenticated";

grant trigger on table "public"."applications" to "authenticated";

grant truncate on table "public"."applications" to "authenticated";

grant update on table "public"."applications" to "authenticated";

grant delete on table "public"."applications" to "service_role";

grant insert on table "public"."applications" to "service_role";

grant references on table "public"."applications" to "service_role";

grant select on table "public"."applications" to "service_role";

grant trigger on table "public"."applications" to "service_role";

grant truncate on table "public"."applications" to "service_role";

grant update on table "public"."applications" to "service_role";

grant delete on table "public"."profiles" to "anon";

grant insert on table "public"."profiles" to "anon";

grant references on table "public"."profiles" to "anon";

grant select on table "public"."profiles" to "anon";

grant trigger on table "public"."profiles" to "anon";

grant truncate on table "public"."profiles" to "anon";

grant update on table "public"."profiles" to "anon";

grant delete on table "public"."profiles" to "authenticated";

grant insert on table "public"."profiles" to "authenticated";

grant references on table "public"."profiles" to "authenticated";

grant select on table "public"."profiles" to "authenticated";

grant trigger on table "public"."profiles" to "authenticated";

grant truncate on table "public"."profiles" to "authenticated";

grant update on table "public"."profiles" to "authenticated";

grant delete on table "public"."profiles" to "service_role";

grant insert on table "public"."profiles" to "service_role";

grant references on table "public"."profiles" to "service_role";

grant select on table "public"."profiles" to "service_role";

grant trigger on table "public"."profiles" to "service_role";

grant truncate on table "public"."profiles" to "service_role";

grant update on table "public"."profiles" to "service_role";

grant delete on table "public"."scholarship_types" to "anon";

grant insert on table "public"."scholarship_types" to "anon";

grant references on table "public"."scholarship_types" to "anon";

grant select on table "public"."scholarship_types" to "anon";

grant trigger on table "public"."scholarship_types" to "anon";

grant truncate on table "public"."scholarship_types" to "anon";

grant update on table "public"."scholarship_types" to "anon";

grant delete on table "public"."scholarship_types" to "authenticated";

grant insert on table "public"."scholarship_types" to "authenticated";

grant references on table "public"."scholarship_types" to "authenticated";

grant select on table "public"."scholarship_types" to "authenticated";

grant trigger on table "public"."scholarship_types" to "authenticated";

grant truncate on table "public"."scholarship_types" to "authenticated";

grant update on table "public"."scholarship_types" to "authenticated";

grant delete on table "public"."scholarship_types" to "service_role";

grant insert on table "public"."scholarship_types" to "service_role";

grant references on table "public"."scholarship_types" to "service_role";

grant select on table "public"."scholarship_types" to "service_role";

grant trigger on table "public"."scholarship_types" to "service_role";

grant truncate on table "public"."scholarship_types" to "service_role";

grant update on table "public"."scholarship_types" to "service_role";

grant delete on table "public"."scholarships" to "anon";

grant insert on table "public"."scholarships" to "anon";

grant references on table "public"."scholarships" to "anon";

grant select on table "public"."scholarships" to "anon";

grant trigger on table "public"."scholarships" to "anon";

grant truncate on table "public"."scholarships" to "anon";

grant update on table "public"."scholarships" to "anon";

grant delete on table "public"."scholarships" to "authenticated";

grant insert on table "public"."scholarships" to "authenticated";

grant references on table "public"."scholarships" to "authenticated";

grant select on table "public"."scholarships" to "authenticated";

grant trigger on table "public"."scholarships" to "authenticated";

grant truncate on table "public"."scholarships" to "authenticated";

grant update on table "public"."scholarships" to "authenticated";

grant delete on table "public"."scholarships" to "service_role";

grant insert on table "public"."scholarships" to "service_role";

grant references on table "public"."scholarships" to "service_role";

grant select on table "public"."scholarships" to "service_role";

grant trigger on table "public"."scholarships" to "service_role";

grant truncate on table "public"."scholarships" to "service_role";

grant update on table "public"."scholarships" to "service_role";

grant delete on table "public"."university_centers" to "anon";

grant insert on table "public"."university_centers" to "anon";

grant references on table "public"."university_centers" to "anon";

grant select on table "public"."university_centers" to "anon";

grant trigger on table "public"."university_centers" to "anon";

grant truncate on table "public"."university_centers" to "anon";

grant update on table "public"."university_centers" to "anon";

grant delete on table "public"."university_centers" to "authenticated";

grant insert on table "public"."university_centers" to "authenticated";

grant references on table "public"."university_centers" to "authenticated";

grant select on table "public"."university_centers" to "authenticated";

grant trigger on table "public"."university_centers" to "authenticated";

grant truncate on table "public"."university_centers" to "authenticated";

grant update on table "public"."university_centers" to "authenticated";

grant delete on table "public"."university_centers" to "service_role";

grant insert on table "public"."university_centers" to "service_role";

grant references on table "public"."university_centers" to "service_role";

grant select on table "public"."university_centers" to "service_role";

grant trigger on table "public"."university_centers" to "service_role";

grant truncate on table "public"."university_centers" to "service_role";

grant update on table "public"."university_centers" to "service_role";


  create policy "Users can create applications for themselves"
  on "public"."applications"
  as permissive
  for insert
  to public
with check ((auth.uid() = student_id));



  create policy "Users can delete their own applications"
  on "public"."applications"
  as permissive
  for delete
  to public
using ((auth.uid() = student_id));



  create policy "Users can see their own applications"
  on "public"."applications"
  as permissive
  for select
  to public
using ((auth.uid() = student_id));



  create policy "Insertar perfil propio"
  on "public"."profiles"
  as permissive
  for insert
  to public
with check ((auth.uid() = id));



  create policy "Users can see their own profile"
  on "public"."profiles"
  as permissive
  for select
  to public
using ((auth.uid() = id));



  create policy "Users can update their own profile"
  on "public"."profiles"
  as permissive
  for update
  to public
using ((auth.uid() = id));



  create policy "Allow public read access to scholarship types"
  on "public"."scholarship_types"
  as permissive
  for select
  to public
using (true);



  create policy "Allow public read access to scholarships"
  on "public"."scholarships"
  as permissive
  for select
  to public
using (true);



  create policy "Allow public read access to university centers"
  on "public"."university_centers"
  as permissive
  for select
  to public
using (true);


CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();



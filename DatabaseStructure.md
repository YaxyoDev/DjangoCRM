### User (asosiy auth model — allaqachon bor) ###

-full_name-
-phone-
-email-
-role- (teacher, pupil, admin, manager, cashier, register)
-password-
-is_active-
-date_joined-

###### ACCOUTNS #############################################################

### AdminProfile ### (OneToOne -> User)

-user- (OneToOne -> User)
-salary- (Decimal)
-status- (active, inactive)
-created_at-
# full_name, phone -> user orqali keladi

### PupilProfile ###   (OneToOne -> User)

-user- (OneToOne -> User)
-parent_phone_number-
-birth_date-
-balance- (Decimal)
-status- (active, frozen, archived)
-created_at-
# full_name, phone -> user orqali keladi


### TeacherProfile ###   (OneToOne -> User)

-user- (OneToOne -> User)
-salary_percent- (Decimal)
-balance- (Decimal)
-subjects- (ManyToMany -> Course)
-status- (active, archived)
-created_at-
# full_name, phone -> user orqali keladi

### ManagerProfile ### (OneToOne -> User)

-user- (OneToOne -> User)
-salary- (Decimal)
-status- (active, inactive)
-created_at-
# full_name, phone -> user orqali keladi

### CashierProfile ### (OneToOne -> User)

-user- (OneToOne -> User)
-salary- (Decimal)
-status- (active, inactive)
-created_at-
# full_name, phone -> user orqali keladi

### RegisterProfile ### (OneToOne -> User)

-user- (OneToOne -> User)
-salary- (Decimal)
-status- (active, inactive)
-created_at-
# full_name, phone -> user orqali keladi

###### EDUCATION #############################################################

### Course ###

-name-
-created_at-


### Room ###

-name-   (ex: Room 1, IT ishxonasi)
-status- (active, inactive)
-created_at-


### Time ###

-days- (choice: mo-we-fr / tu-th-sa / sa-su)
-time_start-
-time_end-


### Group ###

-name-
-course- (FK -> Course)
-price- (Decimal)
-teacher- (FK -> TeacherProfile)
-room- (FK -> Room)
-time- (FK -> Time)
-status- (active, inactive)
-created_at-


### Enrollment ###   (o'quvchi <-> guruh bog'lanishi)

-pupil- (FK -> PupilProfile)
-group- (FK -> Group)
-status- (active, frozen, left)
-joined_at-
# bitta o'quvchi ko'p guruhda, bitta guruhda ko'p o'quvchi


### Payment ###   (to'lov tarixi)

-pupil- (FK -> PupilProfile)
-group- (FK -> Group)        # qaysi guruh uchun (ixtiyoriy)
-amount- (Decimal)
-cashier- (FK -> User)        # qaysi kassir qabul qildi
-created_at-
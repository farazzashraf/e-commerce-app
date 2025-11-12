# 🛍️ Multi-Vendor Thrift Shop Platform

A Django-based e-commerce platform that enables multiple sellers to list products, manage inventory, and fulfill orders through a unified marketplace. Customers can browse thrift items, add them to cart, and complete purchases, while platform administrators control seller approvals and global configurations.
    
> ⚠️ **Note:** This project is currently under development and **not production-ready yet**.

## ✨ Features

### For Customers
- 🔐 Firebase authentication 
- 🔍 Browse and search products with filtering/sorting
- 🛒 Shopping cart (session-based for guests, database-backed for authenticated users)
- 💳 Secure checkout process
- 📧 Order confirmation emails
- 📦 Order tracking and history

### For Sellers
- 🏪 Custom seller dashboard (separate from Django admin)
- 📊 Sales analytics and insights
- 📦 Product management (CRUD operations)
- 🎨 Product variants (color, size, fit)
- 📸 Multiple product images via Supabase storage
- 📋 Order management and fulfillment
- ✅ Approval workflow for new sellers

### For Platform Admins
- 👥 Seller approval system
- 🏷️ Category and subcategory management
- 🎟️ Promo code creation
- 📊 Platform-wide analytics via Django admin

## 🛠️ Tech Stack

### Backend
- **Framework:** Django 5.1.5
- **Database:** PostgreSQL (hosted on Supabase)

### Frontend
- **Templates:** Django Templates
- **Styling:** Tailwind CSS / Custom CSS
- **JavaScript:** Vanilla JS with Firebase SDK

### Authentication & Storage
- **Customer Auth:** Firebase Authentication
- **Seller Auth:** Django Sessions
- **File Storage:** Supabase Storage (product images)
- **Email:** SMTP (Gmail/SendGrid)

### Infrastructure
> ⚠️ **Not Ready Yet**

- **Deployment:** Railway / Render / Heroku
- **Environment Management:** python-decouple

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL (or Supabase account)
- Redis (for caching)
- Firebase project (for authentication)
- Git

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/farazzashraf/e-commerce-app.git
cd e-commerce-app
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET=product-images

# Firebase Admin SDK Path
FIREBASE_CONFIG_PATH=firebase/firebase-admin-sdk.json
```

### 5. Set Up Firebase

#### Get Firebase Admin SDK:
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project → Project Settings → Service Accounts
3. Click "Generate New Private Key"
4. Save the JSON file as `firebase/firebase-admin-sdk.json`

#### Configure Firebase Client:
1. Copy `store/static/js/firebase-config.template.js` to `store/static/js/firebase-config.js`
2. Replace the placeholders with your Firebase web config:
```javascript
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_AUTH_DOMAIN",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID",
    measurementId: "YOUR_MEASUREMENT_ID"
};
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Platform Admin)
```bash
python manage.py createsuperuser
```

### 8. Collect Static Files (Production)
```bash
python manage.py collectstatic
```

### 9. Run Development Server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

## 📁 Project Structure

```
e-commerce-app/
├── ecommerce/              # Django project configuration
│   ├── settings.py         # Main settings (DB, Firebase, Supabase)
│   ├── urls.py             # Root URL routing
│   └── wsgi.py             # WSGI entry point
├── store/                  # Main application
│   ├── models.py           # Database models (User, Product, Order, etc.)
│   ├── views.py            # Request handlers (200+ LOC)
│   ├── urls.py             # URL patterns
│   ├── admin.py            # Django admin customization
│   ├── orm_queries.py      # Service layer (CartService, product queries)
│   ├── templates/          # HTML templates
│   │   ├── home.html       # Product listing
│   │   ├── cart.html       # Shopping cart
│   │   ├── checkout.html   # Checkout page
│   │   └── admin/          # Seller dashboard templates
│   └── static/             # CSS, JS, images
│       ├── css/
│       ├── js/
│       │   └── firebase-config.js  # Firebase client config
│       └── images/
├── firebase/               # Firebase credentials (gitignored)
│   └── firebase-admin-sdk.json
├── .env                    # Environment variables (gitignored)
├── .gitignore
├── requirements.txt
└── manage.py
```

## 👥 User Types & Access

### 1. **Customers**
- **Authentication:** Firebase 
- **Access:** Product browsing, cart, checkout, order history
- **URL:** `/login/`

### 2. **Sellers (Store Admins)**
- **Authentication:** Django sessions (email/password)
- **Access:** Custom dashboard, product management, order fulfillment
- **URL:** `/store-admin/login/`
- **Note:** Requires platform admin approval

### 3. **Platform Admins**
- **Authentication:** Django superuser
- **Access:** Full Django admin, seller approvals, category management
- **URL:** `/admin/`

## 🗄️ Database Models

| Model | Purpose |
|-------|---------|
| `User` | Customer accounts (linked to Firebase UID) |
| `AdminStore` | Seller accounts with approval status |
| `Product` | Product catalog with soft deletion |
| `ProductVariant` | SKU-level variations (color, size, fit) |
| `Category` | Top-level product classification |
| `Subcategory` | Second-level classification |
| `Cart` | Shopping cart items |
| `Order` | Order header with status tracking |
| `OrderItem` | Individual line items in orders |
| `PromoCode` | Discount codes |

## 🔑 Key Features Explained

### Multi-Vendor Architecture
- Each seller has a separate `AdminStore` account
- Products and orders are partitioned by seller
- Sellers have isolated dashboards
- Platform admin approves new sellers

### Hybrid Authentication
- **Customers:** Firebase handles authentication, Django verifies tokens
- **Sellers:** Traditional Django session authentication
- Separate login flows for different user types

### Shopping Cart
- **Anonymous users:** Session-based cart
- **Authenticated users:** Database-backed cart
- Cart merges on login

### Soft Deletion
- Products use `is_deleted` flag instead of actual deletion
- Preserves order history and referential integrity
- Additional flags: `is_active`, `is_verified`

## 📝 API Endpoints (if applicable)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with product listing |
| `/cart/add/` | POST | Add product to cart |
| `/cart/` | GET | View cart |
| `/checkout/` | GET/POST | Checkout page |
| `/place-order/` | POST | Submit order |
| `/admin-dashboard/` | GET | Seller dashboard |
| `/admin-products/` | GET/POST | Product management |
| `/admin-orders/` | GET | Order management |

## 👨‍💻 Author

**Faraz Ashraf**
- GitHub: [@farazzashraf](https://github.com/farazzashraf)

## 🙏 Acknowledgments

- Django Documentation
- Firebase Authentication
- Supabase for database and storage
- Tailwind CSS community

**⭐ If you found this project helpful, please give it a star!**
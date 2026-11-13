# Fake Product Detection
AI-powered Android app that checks product packaging photos for signs of counterfeiting. It reads packaging text (OCR), detects logos and barcodes (YOLO), and compares images with genuine references to flag suspicious products. Built with Android, Spring Boot and FastAPI.

## Backend Product Management API

The Spring Boot backend exposes product reference data under `/api/products`.

### Endpoints

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| `POST` | `/api/products` | Create a product | `201 Created` |
| `GET` | `/api/products` | List products with pagination and sorting | `200 OK` |
| `GET` | `/api/products/{id}` | Get a product by ID | `200 OK` |
| `PUT` | `/api/products/{id}` | Replace all editable product fields | `200 OK` |
| `DELETE` | `/api/products/{id}` | Delete a product | `204 No Content` |

Product creation and full updates require non-blank `brand` (up to 120 characters), `productName` (up to 200), and `category` (up to 100). Optional `barcode` is limited to 64 characters and optional `expectedText` to 5,000 characters.

### Pagination and sorting

`GET /api/products` supports these query parameters:

| Parameter | Default | Rules |
| --- | --- | --- |
| `page` | `0` | Zero or greater |
| `size` | `10` | From 1 to 100 |
| `sortBy` | `id` | `id`, `brand`, `productName`, `category`, `barcode`, or `expectedText` |
| `direction` | `ASC` | `ASC` or `DESC` |

Examples:

```text
GET http://localhost:8080/api/products
GET http://localhost:8080/api/products?page=1&size=5
GET http://localhost:8080/api/products?page=0&size=10&sortBy=brand&direction=ASC
GET http://localhost:8080/api/products?page=0&size=10&sortBy=category&direction=DESC
```

The list response is a Spring Data page with a `content` array and pagination metadata such as `number`, `size`, `totalElements`, and `totalPages`.

### Example requests

Create a product:

```http
POST /api/products
Content-Type: application/json

{
  "brand": "Acme",
  "productName": "Cereal",
  "category": "Food",
  "barcode": "0012345678905",
  "expectedText": "Genuine package text"
}
```

Replace a product:

```http
PUT /api/products/42
Content-Type: application/json

{
  "brand": "Acme",
  "productName": "Cereal",
  "category": "Food",
  "barcode": "0012345678905",
  "expectedText": "Genuine package text"
}
```

Retrieve or delete a product with `GET /api/products/42` or `DELETE /api/products/42`.

### Error responses

Errors use the same JSON structure. Validation and invalid pagination/query parameters return `400 Bad Request`; a missing product returns `404 Not Found`.

```json
{
  "status": 400,
  "error": "Bad Request",
  "message": "brand must not be blank"
}
```

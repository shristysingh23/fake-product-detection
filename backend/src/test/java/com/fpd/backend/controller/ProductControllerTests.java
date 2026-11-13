package com.fpd.backend.controller;

import static org.hamcrest.Matchers.endsWith;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;

import com.fpd.backend.dto.request.ProductCreateRequestDto;
import com.fpd.backend.dto.request.ProductUpdateRequestDto;
import com.fpd.backend.dto.response.ProductResponseDto;
import com.fpd.backend.exception.GlobalExceptionHandler;
import com.fpd.backend.exception.ProductNotFoundException;
import com.fpd.backend.service.ProductService;

class ProductControllerTests {

	private MockMvc mockMvc;
	private ProductService productService;

	@BeforeEach
	void setUp() {
		productService = org.mockito.Mockito.mock(ProductService.class);
		LocalValidatorFactoryBean validator = new LocalValidatorFactoryBean();
		validator.afterPropertiesSet();

		mockMvc = MockMvcBuilders.standaloneSetup(new ProductController(productService))
				.setControllerAdvice(new GlobalExceptionHandler())
				.setValidator(validator)
				.build();
	}

	@Test
	void createProductReturnsCreatedResponseJson() throws Exception {
		ProductResponseDto response = productResponse(42L);
		when(productService.createProduct(any(ProductCreateRequestDto.class))).thenReturn(response);

		mockMvc.perform(post("/api/products")
				.contentType(MediaType.APPLICATION_JSON)
				.content(validCreateRequest()))
				.andExpect(status().isCreated())
				.andExpect(jsonPath("$.id").value(42))
				.andExpect(jsonPath("$.brand").value("Acme"))
				.andExpect(jsonPath("$.productName").value("Cereal"))
				.andExpect(jsonPath("$.category").value("Food"))
				.andExpect(jsonPath("$.barcode").value("0012345678905"))
				.andExpect(jsonPath("$.expectedText").value("Genuine package text"));

		verify(productService).createProduct(any(ProductCreateRequestDto.class));
	}

	@Test
	void createProductReturnsLocationContainingCreatedId() throws Exception {
		when(productService.createProduct(any(ProductCreateRequestDto.class))).thenReturn(productResponse(42L));

		mockMvc.perform(post("/api/products")
				.contentType(MediaType.APPLICATION_JSON)
				.content(validCreateRequest()))
				.andExpect(status().isCreated())
				.andExpect(header().string(HttpHeaders.LOCATION, endsWith("/api/products/42")));
	}

	@Test
	void getAllProductsUsesDefaultPaginationParameters() throws Exception {
		returnEmptyPageForAnyPageable();
		mockMvc.perform(get("/api/products"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.content").isArray())
				.andExpect(jsonPath("$.number").value(0))
				.andExpect(jsonPath("$.size").value(10))
				.andExpect(jsonPath("$.totalElements").value(0));

		verify(productService).getAllProducts(
				PageRequest.of(0, 10, Sort.by(Sort.Direction.ASC, "id")));
	}

	@Test
	void getAllProductsAcceptsCustomPageAndSize() throws Exception {
		returnEmptyPageForAnyPageable();

		mockMvc.perform(get("/api/products").param("page", "1").param("size", "5"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.number").value(1))
				.andExpect(jsonPath("$.size").value(5));

		verify(productService).getAllProducts(
				PageRequest.of(1, 5, Sort.by(Sort.Direction.ASC, "id")));
	}

	@Test
	void getAllProductsSortsByBrandAscending() throws Exception {
		returnEmptyPageForAnyPageable();

		mockMvc.perform(get("/api/products")
				.param("sortBy", "brand")
				.param("direction", "ASC"))
				.andExpect(status().isOk());

		verify(productService).getAllProducts(
				PageRequest.of(0, 10, Sort.by(Sort.Direction.ASC, "brand")));
	}

	@Test
	void getAllProductsSortsByCategoryDescending() throws Exception {
		returnEmptyPageForAnyPageable();

		mockMvc.perform(get("/api/products")
				.param("sortBy", "category")
				.param("direction", "DESC"))
				.andExpect(status().isOk());

		verify(productService).getAllProducts(
				PageRequest.of(0, 10, Sort.by(Sort.Direction.DESC, "category")));
	}

	@Test
	void getAllProductsRejectsNegativePage() throws Exception {
		assertInvalidProductListRequest(
				get("/api/products").param("page", "-1"),
				"Page number must be zero or greater.");
	}

	@Test
	void getAllProductsRejectsSizeZero() throws Exception {
		assertInvalidProductListRequest(
				get("/api/products").param("size", "0"),
				"Page size must be at least 1.");
	}

	@Test
	void getAllProductsRejectsSizeAboveMaximum() throws Exception {
		assertInvalidProductListRequest(
				get("/api/products").param("size", "101"),
				"Page size must not exceed 100.");
	}

	@Test
	void getAllProductsRejectsInvalidDirection() throws Exception {
		assertInvalidProductListRequest(
				get("/api/products").param("direction", "SIDEWAYS"),
				"Direction must be ASC or DESC.");
	}

	@Test
	void getAllProductsRejectsUnsupportedSortField() throws Exception {
		assertInvalidProductListRequest(
				get("/api/products").param("sortBy", "unknown"),
				"Unsupported sort field.");
	}

	@Test
	void getAllProductsRejectsMalformedPageParameter() throws Exception {
		assertInvalidProductListRequest(
				get("/api/products").param("page", "abc"),
				"Page must be a non-negative integer.");
	}

	@Test
	void getAllProductsRejectsMalformedSizeParameter() throws Exception {
		assertInvalidProductListRequest(
				get("/api/products").param("size", "abc"),
				"Size must be an integer between 1 and 100.");
	}

	@Test
	void getProductByIdReturnsProduct() throws Exception {
		when(productService.getProductById(42L)).thenReturn(productResponse(42L));

		mockMvc.perform(get("/api/products/42"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.id").value(42))
				.andExpect(jsonPath("$.brand").value("Acme"))
				.andExpect(jsonPath("$.productName").value("Cereal"))
				.andExpect(jsonPath("$.category").value("Food"))
				.andExpect(jsonPath("$.barcode").value("0012345678905"))
				.andExpect(jsonPath("$.expectedText").value("Genuine package text"));

		verify(productService).getProductById(42L);
	}

	@Test
	void getMissingProductReturnsExistingApiErrorResponse() throws Exception {
		when(productService.getProductById(404L))
				.thenThrow(new ProductNotFoundException("Product with id 404 was not found."));

		mockMvc.perform(get("/api/products/404"))
				.andExpect(status().isNotFound())
				.andExpect(jsonPath("$.status").value(404))
				.andExpect(jsonPath("$.error").value("Not Found"))
				.andExpect(jsonPath("$.message").value("Product with id 404 was not found."));
	}

	@Test
	void invalidCreateRequestReturnsBadRequest() throws Exception {
		mockMvc.perform(post("/api/products")
				.contentType(MediaType.APPLICATION_JSON)
				.content("""
						{
						  "brand": " ",
						  "productName": "Cereal",
						  "category": "Food",
						  "barcode": null,
						  "expectedText": null
						}
						"""))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.status").value(400))
				.andExpect(jsonPath("$.error").value("Bad Request"))
				.andExpect(jsonPath("$.message").value("brand must not be blank"));

		verifyNoInteractions(productService);
	}

	@Test
	void missingProductNameReturnsValidationError() throws Exception {
		mockMvc.perform(post("/api/products")
				.contentType(MediaType.APPLICATION_JSON)
				.content("""
						{
						  "brand": "Acme",
						  "category": "Food"
						}
						"""))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.message").value("productName must not be blank"));

		verifyNoInteractions(productService);
	}

	@Test
	void invalidCategoryLengthReturnsValidationError() throws Exception {
		String invalidCategoryRequest = validCreateRequest()
				.replace("\"category\": \"Food\"", "\"category\": \"" + "x".repeat(101) + "\"");

		mockMvc.perform(post("/api/products")
				.contentType(MediaType.APPLICATION_JSON)
				.content(invalidCategoryRequest))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.message").value("category size must be between 0 and 100"));

		verifyNoInteractions(productService);
	}

	@Test
	void updateProductReturnsUpdatedProduct() throws Exception {
		ProductResponseDto updatedProduct = new ProductResponseDto(
				42L, "New Acme", "New Cereal", "Breakfast", "0098765432105", "Updated package text");
		when(productService.updateProduct(eq(42L), any(ProductUpdateRequestDto.class)))
				.thenReturn(updatedProduct);

		mockMvc.perform(put("/api/products/42")
				.contentType(MediaType.APPLICATION_JSON)
				.content(validUpdateRequest()))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.id").value(42))
				.andExpect(jsonPath("$.brand").value("New Acme"))
				.andExpect(jsonPath("$.productName").value("New Cereal"))
				.andExpect(jsonPath("$.category").value("Breakfast"))
				.andExpect(jsonPath("$.barcode").value("0098765432105"))
				.andExpect(jsonPath("$.expectedText").value("Updated package text"));

		verify(productService).updateProduct(eq(42L), any(ProductUpdateRequestDto.class));
	}

	@Test
	void updateMissingProductReturnsExistingApiErrorResponse() throws Exception {
		when(productService.updateProduct(eq(404L), any(ProductUpdateRequestDto.class)))
				.thenThrow(new ProductNotFoundException("Product with id 404 was not found."));

		mockMvc.perform(put("/api/products/404")
				.contentType(MediaType.APPLICATION_JSON)
				.content(validUpdateRequest()))
				.andExpect(status().isNotFound())
				.andExpect(jsonPath("$.status").value(404))
				.andExpect(jsonPath("$.error").value("Not Found"))
				.andExpect(jsonPath("$.message").value("Product with id 404 was not found."));
	}

	@Test
	void invalidUpdateRequestReturnsBadRequestWithoutCallingService() throws Exception {
		mockMvc.perform(put("/api/products/42")
				.contentType(MediaType.APPLICATION_JSON)
				.content("""
						{
						  "brand": "Acme",
						  "productName": " ",
						  "category": "Food",
						  "barcode": null,
						  "expectedText": null
						}
						"""))
				.andExpect(status().isBadRequest());

		verifyNoInteractions(productService);
	}

	@Test
	void deleteProductReturnsNoContentWithEmptyBody() throws Exception {
		mockMvc.perform(delete("/api/products/42"))
				.andExpect(status().isNoContent())
				.andExpect(content().string(""));

		verify(productService).deleteProduct(42L);
	}

	@Test
	void deleteMissingProductReturnsExistingApiErrorResponse() throws Exception {
		org.mockito.Mockito.doThrow(new ProductNotFoundException("Product with id 404 was not found."))
				.when(productService).deleteProduct(404L);

		mockMvc.perform(delete("/api/products/404"))
				.andExpect(status().isNotFound())
				.andExpect(jsonPath("$.status").value(404))
				.andExpect(jsonPath("$.error").value("Not Found"))
				.andExpect(jsonPath("$.message").value("Product with id 404 was not found."));
	}

	private String validCreateRequest() {
		return """
				{
				  "brand": "Acme",
				  "productName": "Cereal",
				  "category": "Food",
				  "barcode": "0012345678905",
				  "expectedText": "Genuine package text"
				}
				""";
	}

	private String validUpdateRequest() {
		return """
				{
				  "brand": "New Acme",
				  "productName": "New Cereal",
				  "category": "Breakfast",
				  "barcode": "0098765432105",
				  "expectedText": "Updated package text"
				}
				""";
	}

	private ProductResponseDto productResponse(Long id) {
		return new ProductResponseDto(id, "Acme", "Cereal", "Food",
				"0012345678905", "Genuine package text");
	}

	private void returnEmptyPageForAnyPageable() {
		when(productService.getAllProducts(any(Pageable.class)))
				.thenAnswer(invocation -> Page.empty(invocation.getArgument(0)));
	}

	private void assertInvalidProductListRequest(
			org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder request,
			String message) throws Exception {
		mockMvc.perform(request)
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.status").value(400))
				.andExpect(jsonPath("$.error").value("Bad Request"))
				.andExpect(jsonPath("$.message").value(message));

		verifyNoInteractions(productService);
	}
}

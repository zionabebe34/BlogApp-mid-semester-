
describe('User Authentication End-to-End Flow', () => {

  it('Should successfully sign up, log in, and view the profile page', () => {
    // Arrange - prepare test data
    // Generate a short random string so the email is unique on every run (prevents DB conflicts)
    const uniqueId = Math.random().toString(36).substring(2, 8);
    const fakeUser = {
      name: 'Cypress Tester',
      email: `cypress_e2e_${uniqueId}@example.com`,
      password: 'SecurePass123!'
    };

    // ----------------------------
    // 1. Signup step
    // ----------------------------
    // Act: navigate to the signup page and fill in the form
    cy.visit('http://localhost:5173/signup');

    // Fill in the fields
    cy.get('input[placeholder*="name"]').type(fakeUser.name);
    cy.get('input[type="email"]').type(fakeUser.email);
    cy.get('input[type="password"]').eq(0).type(fakeUser.password);
    cy.get('input[type="password"]').eq(1).type(fakeUser.password);
    cy.get('button[type="submit"]').click();

    // Assert: signup succeeded and the app redirected to the Login page
    cy.url().should('include', '/Login');

    // ----------------------------
    // 2. Login step
    // ----------------------------
    // Act: fill in the credentials of the user we just registered
    cy.get('input[type="email"]').type(fakeUser.email);
    cy.get('input[type="password"]').type(fakeUser.password);
    cy.get('button[type="submit"]').click();

    // Assert: login succeeded and we left the Login page
    cy.url().should('not.include', '/Login');

    // ----------------------------
    // 3. Profile step
    // ----------------------------
    // Act: click the Profile link in the top nav (preserves React currentUser state)
    cy.contains('a', 'Profile').click();

    // Assert: data returned from the real backend is displayed on screen
    cy.contains(fakeUser.name).should('be.visible');
    cy.contains(fakeUser.email).should('be.visible');
  });

});

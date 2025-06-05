from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless

def resolver_recaptcha(api_key, site_key, url):
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key(api_key)
    solver.set_website_url(url)
    solver.set_website_key(site_key)

    token = solver.solve_and_return_solution()
    if token != 0:
        return token
    else:
        print(f"Erro ao resolver o captcha: {solver.error_code}")
        return None

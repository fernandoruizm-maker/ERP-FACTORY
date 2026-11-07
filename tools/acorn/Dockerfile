# Preparation only: acorn-8.19.0.tgz is deliberately NOT supplied or downloaded.
FROM node@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9
WORKDIR /opt/parser
COPY acorn-8.19.0.tgz /opt/parser/acorn.tgz
RUN node -e "const f=require('node:fs'),c=require('node:crypto');if(c.createHash('sha512').update(f.readFileSync('acorn.tgz')).digest('base64')!=='oJlA3XiRm7Cyk6qFD2Jn8ak9B7jSy0qy00ADO3+8dpT0LSjFihQYv4C02LFCSYJV3Q37xYwwRy5m+IpIiUzqWw==')process.exit(1)" \
    && mkdir acorn && tar -xzf acorn.tgz --strip-components=1 -C acorn
COPY analyze.mjs cli.mjs /opt/parser/
USER 65534:65534
ENTRYPOINT ["node", "/opt/parser/cli.mjs"]

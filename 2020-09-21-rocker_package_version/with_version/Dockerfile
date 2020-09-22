FROM rocker/tidyverse:4.0.0

RUN wget https://cran.r-project.org/src/contrib/Archive/reticulate/reticulate_1.15.tar.gz

RUN install2.r --error \
	--deps rappdirs \
	reticulate_1.15.tar.gz \
	&& rm -rf /tmp/downloaded_packages/ /tmp/*.rds
